import time
import datetime
from datetime import date, datetime
from odoo import api, models, _
from odoo.exceptions import UserError


class MaintenanceRequestReportTemplate(models.AbstractModel):
    _name = 'report.mbk_fm.maintenance_request_report_template'
    _description = 'Maintenance Request Report Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        final_maintainence_ids = []
        docs = self.env['mbk_fm.ticket'].search([]).filtered(lambda r: (data['from_date'] <= str(r.request_date) <= data['to_date']))
        if data['state'] and docs:
            print('chdsjgcgcsjcbkjck', data['state'])
            if data['state'] == 'todo':
                print('chdsjgcgcsjcbkjck', docs, data['state'], docs.filtered(lambda r: (r.state not in ['done', 'cancel'])))
                docs = docs.filtered(lambda r: (r.state not in ['done','cancel']))
            if data['state'] != 'todo':
                docs = docs.filtered(lambda r: (data['state'] == r.state))
        if data['case_type'] and docs:
            docs = docs.filtered(lambda r: (data['case_type'] == r.ticket_type_id.id))
        if data['team_id'] and docs:
            docs = docs.filtered(lambda r: (data['team_id'] == r.team_id.id))
        if data['unit_id'] and docs:
            docs = docs.filtered(lambda r: (data['unit_id'] == r.unit_id.id))
        if data['property_id'] and docs:
            docs = docs.filtered(lambda r: (data['property_id'] == r.property_id.id))
        if data['priority'] and docs:
            docs = docs.filtered(lambda r: (data['priority'] == r.priority))
        if data['technician_id'] and docs:
            docs = docs.filtered(lambda r: (data['technician_id'] == r.technician_id.id))
        if data['mode_of_contact'] and docs:
            docs = docs.filtered(lambda r: (data['mode_of_contact'] == r.mode_of_contact))
        # if data['close_date'] and docs:
        #     docs = docs.filtered(lambda r: (data['close_date'] == r.close_date))
        return {
            'doc_model': 'mbk_fm.ticket',
            'data': data,
            'docs': docs,
            'optional_close_date': data['optional_close_date'],
            'optional_complaint_reg_by': data['optional_complaint_reg_by'],
            'optional_details_of_complaint': data['optional_details_of_complaint'],
            'optional_customer': data['optional_customer'],
            'optional_techicians': data['optional_techicians'],
            'optional_mode_of_contact': data['optional_mode_of_contact'],
        }


class MaterialRequestReport(models.AbstractModel):
    _name = 'report.mbk_fm.mr'
    _description = 'Material Request Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_fm.material_request'].browse(docids)
        web_base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # mr_url = (web_base_url + "/web#id=%s&model=mbk_fm.material_request&view_type=form") % docs.id
        mr_url = ("http://adhwv.ddns.net:8070/web#id=%s&model=mbk_fm.material_request&view_type=form") % docs.id

        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_fm.material_request',
            'docs': docs,
            'mr_url': mr_url,
        }
