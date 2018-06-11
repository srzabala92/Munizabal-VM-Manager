#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Práctica Final - Virtualización y Escalabilidad de Servidores
# Curso 2017/18
# Alumnos : David Municio Durán y Sergio Zabala Mesonero

# En este paquete se implementa la clase "GestiónVMS", que será la encargada de recoger
# las funciones que llamarán a la API de Xen Server.
# Dichas funciones serán:

# 1) Listado de todas las Máquinas Virtuales existentes en el servidor.
# 2) Creación de una nueva máquina virtual a partir de un template elegido por el usuario.
# 3) Borrado de una máquina virtual del servidor dado su nombre.
# 4) Encendido de una máquina dado su UUID
# 5) Apagado de una máquina dado su UUID 
# 6) Listado de los templates existentes en XenServer a partir de los cuales crear una nueva VM

import sys
import ssl
import XenAPI
import provision

class GestionVMS:
	#session = None
	def __init__(self):
		print "Creando objeto 'GestionVMs'...."
		#Create new SSL session
		if sys.version_info >= (2, 7, 9):
			ssl._create_default_https_context = ssl._create_unverified_context
		#Create new XenAPI Session from Server 74
		#For security,credentials removed
		#self.session = XenAPI.Session("https://SERVER.IP.ADDR")
		#self.session.xenapi.login_with_password("user", "password", "1.0", "xen-api-scripts-install.py")
		print "OK:Creado objeto 'GestionVMs'"
	def list_vms(self):
		'''Function to create a list with existing VMs on server (not templates).
		Returns:
			list : List in which item is a dictionary with main values of each VM on server.
		'''
		hosts = self.session.xenapi.VM.get_all()
		#Create a list with all VMs
		lista_vms = []
		for _host in hosts:
			#Create a dictionary with VM values
			datos_vm = dict()
			#Obtain VM record
			item = self.session.xenapi.VM.get_record(_host)
			#Filter templates
			if item['is_control_domain'] is False \
			and not item["is_a_template"]:
				datos_vm['nombre'] = [item['name_label']]
				datos_vm['estado'] = ['Apagada'] if item['power_state'] == 'Halted' else "Encendida"
				datos_vm['memoria'] = [int(item['memory_static_max'])/1024/1024]
				datos_vm['uuid'] = [item['uuid']]
				#TODO - Calcular Uso del CPU
				datos_vm['cpu'] = [item['VCPUs_max']]
				lista_vms.append(datos_vm)
		return lista_vms
	def list_templates(self):
		'''Function what makes a new dictionary of default templates on server.
		Returns:
			dictionary : Dictionary with default templates (key = name , value = uuid) to user to select an existing one (to create a new VM)
		'''
		hosts = self.session.xenapi.VM.get_all()
		lista_templates=[]
		dict_temp = dict()
		for _host in hosts:
			item = self.session.xenapi.VM.get_record(_host)
			if item['is_control_domain'] is False \
			and item["is_a_template"] and item["name_label"].startswith("[Munizabal]"):
				dict_temp[item['name_label'][12:]] = [item['uuid']]
		return dict_temp

	def crear_vm(self,nombre,template_uuid):
		''' This function is used to create a new VM from a given template.
			The name will be spicified by the user.
		Args:
			nombre (string) : Name of the VM.
			template_uuid (string) : UUID of the selected template.
		Returns:
			string : UUID of the created Virtual Machine
		'''
		# Choose the PIF with the alphabetically lowest device
		# (we assume that plugging the debian VIF into the same network will allow
		# it to get an IP address by DHCP)

		pifs = self.session.xenapi.PIF.get_all_records()
		lowest = None
		for pifRef in pifs.keys():
			if (lowest is None) or (pifs[pifRef]['device'] < pifs[lowest]['device']):
				lowest = pifRef
				print "Choosing PIF with device: ", pifs[lowest]['device']
				network = self.session.xenapi.PIF.get_network(lowest)
		#Obtain template item by given name
		temp = self.session.xenapi.VM.get_by_uuid(template_uuid)
		vm = self.session.xenapi.VM.clone(temp, nombre)
		vif = { 'device': '1',
				'network': network,
				'VM': vm,
				'MAC': "",
				'MAC_autogenerated' : True,
				'MTU': "1500",
				"qos_algorithm_type": "",
				"qos_algorithm_params": {},
				"other_config": {} 
				}
		self.session.xenapi.VIF.create(vif)
		self.session.xenapi.VM.set_PV_args(vm, "non-interactive")
		print "Choosing an SR to instantiate the VM's disks"
		pool = self.session.xenapi.pool.get_all()[0]
		default_sr = self.session.xenapi.pool.get_default_SR(pool)
		default_sr = self.session.xenapi.SR.get_record(default_sr)
		print "Choosing SR: %s (uuid %s)" % (default_sr['name_label'], default_sr['uuid'])
		#spec = provision.getProvisionSpec(self.session, vm)
		#spec.setSR(default_sr['uuid'])
		#provision.setProvisionSpec(self.session, vm, spec)
		self.session.xenapi.VM.provision(vm)
		#self.session.xenapi.VM.start(vm, False, True)
		print "Fin...."
		return self.session.xenapi.VM.get_uuid(vm)

	def details_vm(self,uuid):
		print "details en gestion_vms"
		params = []
		vms = self.session.xenapi.VM.get_all_records()
		for vm in vms:
			record = vms[vm]
			if record["uuid"] == uuid:
				params.append(record["uuid"])
				params.append(record["name_label"])
				params.append(record["name_description"])
				params.append(record["reference_label"])
				params.append(record["power_state"])
				params.append(record["is_a_template"])
				
		return params

	def remove_vm(self,uuid):
		'''Function to delete an existing VM 
		Args:
			uuid (string) : UUID identifier of the machine 
		'''
		vm = self.session.xenapi.VM.get_by_uuid(uuid)
		self.session.xenapi.VM.destroy(vm)
	def start_vm(self,uuid):
		'''Function to power on an existing VM 
		Args:
			uuid (string) : UUID identifier of the machine 
		'''
		vm = self.session.xenapi.VM.get_by_uuid(uuid)
		self.session.xenapi.VM.start(vm, False, True)

	def stop_vm(self,uuid):
		'''Function to power off an existing VM 
		Args:
			uuid (string) : UUID identifier of the machine 
		'''
		vm = self.session.xenapi.VM.get_by_uuid(uuid)
		self.session.xenapi.VM.shutdown(vm)

	def config_vm(self,uuid,memoria,CPUs):
		'''Function to assign maximum memory and the maximum number of Virtual CPUs to 
		   a VM identified by the UUID
		Args:
			uuid (string) : UUID identifier of the machine 
			memoria (int) : Dynamic Max = Dynamic Min = Static Max Memory for the VM (MB)
			CPUs (int) : Maximum number of CPUs assigned for the VM  
		'''
		#Obtaining the uunstance of the selected VM by UUID
		vm = self.session.xenapi.VM.get_by_uuid(uuid)
		registro = self.session.xenapi.VM.get_record(vm)
		#Calculating memory in Bytes
		MB = long(memoria*1024*1024)
		#If selected memory by user is minor than current static min it won't apply
		if MB > registro['memory_static_min']:
			self.session.xenapi.VM.set_memory_dynamic_max(vm,memoria)
			self.session.xenapi.VM.set_memory_dynamic_min(vm,memoria)
			self.session.xenapi.VM.set_memory_static_max(vm,memoria)
		self.session.xenapi.VM.set_VCPUs_at_startup(vm,1)
		self.session.xenapi.VM.set_VCPUs_max(vm,CPUs)

