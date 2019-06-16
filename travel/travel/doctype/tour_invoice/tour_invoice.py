# -*- coding: utf-8 -*-
# Copyright (c) 2019, Bilal Ghayad and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import string, random, re
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.general_ledger import delete_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe import utils, _

#class TourInvoice(Document):
class TourInvoice(AccountsController):
#	pass

	def validate(self):
		self.title = self.customer_name
#
#		i = 0
#		for d in self.items:
#			j = i + 1
#			i = i + 1
#			while j < len(self.items):
#				if d.ticket_no == self.items[j].get('ticket_no'):
#					frappe.throw(_("Ticket No {0} is duplicated with row number {1}"). format(d.ticket_no, j+1));
#				j = j+1
#				
#			parent = frappe.db.get_value("Ticket Invoice Ticket",{"ticket_no": d.ticket_no, "docstatus": ["!=", 2], "parent": ["!=", self.name]}, "parent")
#			if parent:
#				frappe.throw(_("Duplicated Ticket No is not allowed. Ticket No {0} is already existed in Ticket Invoice No {1}"). 
#						format(d.ticket_no, parent))
#			if d.ticket_no:
#				carrier_no = frappe.db.get_value("Carrier Settings",{"carrier_no": d.ticket_no.split('-')[0]}, "carrier_no")
#				if not carrier_no:
#					frappe.throw(_("Carrier No {0} is not existed for any carrier"). format(d.ticket_no.split('-')[0]))
#			elif not d.ticket_no:
#				frappe.throw(_("Ticket No should not be empty. Please check ticket no at row # {0}"). format(i))
		self.set_status()
	def on_cancel(self):
		delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
		self.set_status()

	def on_submit(self):
		if (self.cust_grand_total != 0):
			self.make_gl_entries()
		self.set_status()

	def make_gl_entries(self):
#		customer_against = self.supplier + " + " + self.income_account

		gl_entry = []

#		customer_gl_entries =  self.get_gl_dict({
		gl_entry.append(self.get_gl_dict({
			"account": self.receivable_account,
#			"against": customer_against,
			"party_type": "Customer",
			"party": self.customer,
			"debit": self.cust_grand_total,
			"debit_in_account_currency": self.cust_grand_total,
			"against_voucher": self.name,
			"against_voucher_type": self.doctype,
			"cost_center": self.cost_center
		}))

		gl_entry.append(self.get_gl_dict({
			"account": self.def_sales_vat_acc,
			"against": self.customer,
			"credit": self.customer_vat,
			"credit_in_account_currency": self.customer_vat,
			"against_voucher": self.name,
			"against_voucher_type": self.doctype,
			"cost_center": self.cost_center
		}))

		supplier_against = self.customer + " - " + self.income_account
		suppliers_gl_entry = frappe.get_doc("Tour Invoice", self.name).get('items')
		for d in suppliers_gl_entry:

#			supplier_gl_entry = self.get_gl_dict({
			gl_entry.append(self.get_gl_dict({
				"account": self.payable_account,
				"against": supplier_against,
				"party_type": "Supplier",
				"party": d.get('supplier'),
				"credit": d.get('supp_total_av'),
				"credit_in_account_currency": d.get('supp_total_av'),
				"against_voucher": self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center
			}))

			gl_entry.append(self.get_gl_dict({
				"account": self.def_purchase_vat_acc,
				"against": d.get('supplier'),
				"debit": d.get('supp_vat'),
				"debit_in_account_currency": d.get('supp_vat'),
				"against_voucher": self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center
			}))

#		income_against = self.customer + " - " + self.supplier 

#		income_gl_entry = self.get_gl_dict({
		gl_entry.append(self.get_gl_dict({
			"account": self.income_account,
#			"against": income_against,
			"credit": self.c_s,
			"credit_in_account_currency": self.c_s,
			"against_voucher": self.name,
			"against_voucher_type": self.doctype,
			"cost_center": self.cost_center
		}))

		if float(self.paid_amount) > 0:
#			payment_gl_entry = []
			payments = frappe.get_doc("Tour Invoice", self.name).get('payments')
			for d in payments:
				gl_entry.append(self.get_gl_dict({
					"account": d.get('account'),
					"against": self.customer,
					"debit": d.get('amount'),
					"debit_in_account_currency": d.get('amount'),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center
				}))

				gl_entry.append(self.get_gl_dict({
					"account": self.receivable_account,
					"against": d.get('account'),
					"party_type": "Customer",
					"party": self.customer,
					"credit": d.get('amount'),
					"credit_in_account_currency": d.get('amount'),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center
				}))

#		make_gl_entries([customer_gl_entries, supplier_gl_entry, income_gl_entry], cancel=(self.docstatus == 2),
#				update_outstanding="No", merge_entries=False)

		make_gl_entries(gl_entry, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=True)


@frappe.whitelist()
def get_company_accounts(company):

	company_accounts = frappe.db.sql("""select default_receivable_account, default_payable_account, default_income_account, cost_center
						from `tabCompany` where company_name = %s""", (company), as_dict=True)

#	frappe.msgprint("The company accounts are: {0}". format(company_accounts))
#	return receivable_acc, payable_acc
	return company_accounts

@frappe.whitelist()
def get_employee_id(user_id):

#	frappe.msgprint("Session ID {0}". format(user_id))
	employee_id = frappe.db.get_value("Employee", {'user_id': user_id}, "name")
	employee_name = frappe.db.get_value("Employee", {'user_id': user_id}, "employee_name")

#	frappe.msgprint("Employee ID is {0} and Name is {1}". format(employee_id, employee_name))
#	return receivable_acc, payable_acc
	return employee_id, employee_name
