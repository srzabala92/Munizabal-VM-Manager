#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Práctica Final - Virtualización y Escalabilidad de Servidores
# Curso 2017/18
# Alumnos : David Municio Durán y Sergio Zabala Mesonero
# En este paquete se implementa la clase "GUI", que será
# la encargada de generar una interfaz que sirva de medio de interacción
# entre el usuario y las funciones de la API de XenServer,
# incluyendo la clase "GestionVMs",encargada de las acciones sobre
# el servidor.
# En esta clase se han definido las funciones que serán llamadas
# desde los botones y campos de la interfaz.

try:
	import Tkinter as tk  # for python 2
	import tkMessageBox as mensaje
except:
	import Tkinter as tk  # for python 2
	import Tkinter.messagebox as mensaje
import pygubu
import gestion_vms
import time

class GUI:
	def __init__(self, master):
		print "Creando objeto 'GUI'...."
		#Create an instance of "GestionVMs"
		self.gestorVMs = gestion_vms.GestionVMS()
		self.dict_templates = self.gestorVMs.list_templates()
		#gestorVMs = gestion_vms.GestionVMS()
		#1: Create a builder
		self.builder = builder = pygubu.Builder()
		#2: Load an ui file
		builder.add_from_file('interfaz.ui')
		#3: Create the widget using a master as parent
		self.mainwindow = builder.get_object('Frame_1', master)
		self.creacion = builder.get_object('creacion')
		self.creacion.withdraw() #La ventana de creación permanece oculta
		self.creacion.protocol("WM_DELETE_WINDOW",self.creacion.withdraw)#Se asigna el manejador del protocolo de cerrar ventana la función ocultar
		master.protocol("WM_DELETE_WINDOW",master.destroy)
		self.name_in = builder.get_object('name_in')
		self.mem_in = builder.get_object('mem_in', master)
		self.cpus_in = builder.get_object('cpus_in')
		self.template_menu = builder.get_object('template_menu')
		
		#4: Create the widget using a master as parent for details frame
		self.details = builder.get_object('details')
		self.details.withdraw()
		self.details.protocol("WM_DELETE_WINDOW",self.details.withdraw)#Se asigna el manejador del protocolo de cerrar ventana la función ocultar
		master.protocol("WM_DELETE_WINDOW",master.destroy)
		self.entry_details_uuid = builder.get_object('entry_details_uuid')
		self.entry_details_nombre = builder.get_object('entry_details_nombre')
		self.entry_details_name_description = builder.get_object('entry_details_name_description')
		self.entry_details_so = builder.get_object('entry_details_so')
		self.entry_details_estate = builder.get_object('entry_details_estate')
		self.entry_details_isTemplate = builder.get_object('entry_details_isTemplate')

		#Insert icons into buttons
		self.on = builder.get_object('on')
		photo = tk.PhotoImage(file="poweron.png")
		self.on.config(image=photo)
		self.on.image = photo
		#-------------------
		self.off = builder.get_object('off')
		photo = tk.PhotoImage(file="poweroff.png")
		self.off.config(image=photo)
		self.off.image = photo
		#--------------------
		self.logo = builder.get_object('logo')
		photo = tk.PhotoImage(file="logo.png")
		self.logo.config(image=photo)
		self.logo.image = photo
		#----------------------
		self.create = builder.get_object('create')
		photo = tk.PhotoImage(file="crear.png")
		self.create.config(image=photo)
		self.create.image = photo
		#----------------------
		self.create = builder.get_object('button_details')
		photo = tk.PhotoImage(file="details.png")
		self.create.config(image=photo)
		self.create.image = photo		
		#Obtain'TreeView' object(List of VMs)
		self.treeview = builder.get_object('lista_vm')
		self.delete = builder.get_object('delete')
		photo = tk.PhotoImage(file="borrado.png")
		self.delete.config(image=photo)
		self.delete.image = photo
		#List all VM templates
		for k,v in sorted(self.dict_templates.items()):
			self.template_menu["values"] = list(self.template_menu["values"]) + [k]
		self.refresh_btn()
		builder.connect_callbacks(self)
		print "OK:Creado objeto 'GUI'"

	def remove_btn(self):
		''' Function to assign to 'delete button' behaviour, which deletes the selected VM'''
		for item in self.treeview.selection():
			self.gestorVMs.remove_vm(self.treeview.set(item,'uuid'))
			self.treeview.delete(item)

	def power_on_btn(self):
		''' Function to assign to 'power on button' behaviour, which
		is responsible for switching on a selected VM on the list'''
		for item in self.treeview.selection():
			#Encender Máquina Virtual 
			if self.treeview.set(item,'status') != "Encendida":
				self.gestorVMs.start_vm(self.treeview.set(item,'uuid'))
				self.treeview.set(item,'status',"Encendida")
			else: 
				mensaje.showerror("Error", "La máquina debe estar apagada para poder encenderse.")
	def power_off_btn(self):
		''' Function to implement 'power off button', which
		is responsible for switching off a selected VM on the list'''
		for item in self.treeview.selection():
			#Apagar Máquina Virtual (si está encendida)
			if self.treeview.set(item,'status') != "Apagada":
				self.gestorVMs.stop_vm(self.treeview.set(item,'uuid'))
				self.treeview.set(item,'status',"Apagada")
			else: 
				mensaje.showerror("Error", "La máquina debe estar encendida para poder apagarse.")
	def create_vm_btn(self):
		''' Function to implement 'create button', which open a new
		window to introduce parameters of the new VM'''
		self.name_in.delete(0,tk.END)
		self.cpus_in.delete(0,tk.END)
		self.mem_in.delete(0,tk.END)
		#Volver a mostrar el formulario de creación
		self.creacion.deiconify() 

	def details_vm_btn(self):
		''' Function to implement 'details button', which open a new
		window to show parameters of the new VM'''
		for item in self.treeview.selection():
			print self.treeview.set(item,'uuid')
			self.params = self.gestorVMs.details_vm(self.treeview.set(item,'uuid'))
		
			#limpiando valores anteriores
			self.entry_details_uuid.delete(0,tk.END)
			self.entry_details_nombre.delete(0,tk.END)
			self.entry_details_name_description.delete(0,tk.END)
			self.entry_details_so.delete(0,tk.END)
			self.entry_details_estate.delete(0,tk.END)
			self.entry_details_isTemplate.delete(0,tk.END)

			#insertando valores en los inputs
			self.entry_details_uuid.insert(tk.END, self.params[0])
			self.entry_details_nombre.insert(tk.END, self.params[1])
			self.entry_details_name_description.insert(tk.END, self.params[2])
			self.entry_details_so.insert(tk.END, self.params[3])
			self.entry_details_estate.insert(tk.END, self.params[4])
			if self.params[5]:
				template = "Sí"
			else:
				template = "No"
			self.entry_details_isTemplate.insert(tk.END, template)

			self.details.deiconify() 

	def ok_create(self):
		'''Function to confirm a new VM creation,once introduced values for the new VM'''
		#Comprobar que todos los campos estén completos
		if self.name_in.get() == "" or len(self.name_in.get()) > 15:		
			mensaje.showerror("Error al crear", "Debe introducir un nombre válido (menos de 15 caracteres).")
		elif self.mem_in.get() == "" or self.mem_in.get().isdigit() == False or (128 <= int(self.mem_in.get()) <= 3072) == False:
			mensaje.showerror("Error al crear", "Debe introducir un valor numérico de memoria entre 128 y 3072 MB.")
		elif self.cpus_in.get() == "" or self.cpus_in.get().isdigit() == False or (1 <= int(self.cpus_in.get()) <= 6) == False:
			mensaje.showerror("Error al crear", "Debe introducir un número de CPUs entre 1 y 6.")
		elif self.template_menu.get() == "":
			mensaje.showerror("Error al crear", "Debe seleccionar un template de la lista.")
		#Obtener datos de la máquina y añadirlos a la lista
		else:
			template_uuid = self.dict_templates[self.template_menu.get()][0]
			uuid = self.gestorVMs.crear_vm(self.name_in.get(),template_uuid)
			print uuid
			self.gestorVMs.config_vm(uuid,int(self.mem_in.get()),int(self.cpus_in.get()))
			self.creacion.withdraw()
			self.treeview.insert("",tk.END,values=(self.name_in.get(),"Apagada",self.mem_in.get(),"0%",uuid))
	def refresh_btn(self):
		''' Function to implement 'Refrescar' button, to list all the VMs
		availables on server in GUI'''
		#Erase all content
		self.treeview.delete(*self.treeview.get_children())
		lista_vms = self.gestorVMs.list_vms()
		#Recorrer la lista (cada elemento es un diccionario con los datos de la Máquina)
		for vm in lista_vms:
			self.treeview.insert("",tk.END,values=(vm['nombre'],vm['estado'],vm['memoria'],"0%",vm['uuid']))

if __name__ == '__main__':
	print "Iniciando 'Gestor MuniZabal'..."
	root = tk.Tk()
	root.title("Gestión de Máquinas Virtuales - Munizabal")
	app = GUI(root)
	root.mainloop()
	print "Saliendo..."
