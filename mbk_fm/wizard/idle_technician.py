# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FMIdleTechnician(models.TransientModel):
    _name = 'mbk_fm.idle_technician'
    _description = 'View ideal technician details '

    status = fields.Selection(
        [('idle', 'Idle Technician'), ('working', 'Working Technician'), ('inactive', 'Inactive Technician')],
        string='Technician Status', default="idle")

    def action_view_idle_tech(self):
        main_rec = self.env['hr.employee'].search(
            [('department_id.name', '=', 'Maintenance'), ('active', '=', True)]).ids
        tickets = self.env['mbk_fm.ticket'].search([('is_in_progress', '=', True), ('active', '=', True)])

        active_tech_ids = []
        for line in tickets:
            for tech in line.member_ids:
                if tech.id not in active_tech_ids:
                    active_tech_ids.append(tech.id)
                if tech.id in main_rec:
                    main_rec.remove(tech.id)

        tech = self._fields['status'].selection
        tech_dict = dict(tech)
        name = tech_dict.get(self.status)

        if self.status in ('idle', 'inactive'):
            active = False
            if self.status == 'inactive':
                all_activity = self.env['mbk_fm.ticket.activity.line'].search([('member_ids', '!=', False)])
                for line in all_activity:
                    for tech in line.member_ids:
                        if tech.id not in active_tech_ids:
                            active_tech_ids.append(tech.id)
                        if tech.id in main_rec:
                            main_rec.remove(tech.id)
        else:
            active = True


        return {
            'name': name,
            'view_mode': 'tree',
            'res_model': 'hr.employee',
            'view_id': self.env.ref('mbk_fm.view_mbk_fm_technician_tree').id,
            'search_view_id': (self.env.ref('mbk_fm.view_mbk_fm_technician_search').id, 'Technician Status'),
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', active_tech_ids if active else main_rec)],
        }
