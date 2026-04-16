from odoo import api, models, _
from datetime import datetime, timedelta
from dateutil import relativedelta


class LeaseOfferReport(models.AbstractModel):
    _name = 'report.mbk_pms.lease_offer_report'
    _description = 'Lease Offer Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.lease_offer'].browse(docids)
        date1 = datetime.strptime(str(docs.start_date), '%Y-%m-%d')
        date2 = datetime.strptime(str(docs.expiry_date), '%Y-%m-%d') + timedelta(days=1)
        delta = relativedelta.relativedelta(date2, date1)
        contract_period = str(delta.years)+' Year' if delta.years > 0 else ''
        contract_period += str(delta.months) + ' Months' if delta.months > 0 else ''
        contract_period += str(delta.days) + ' Days' if delta.days > 0 else ''
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.lease_offer',
            'docs': docs,
            'contract_period': contract_period,
        }


class ReceiptVoucherReport(models.AbstractModel):
    _name = 'report.mbk_pms.receipt_voucher_report'
    _description = 'Receipt Voucher Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.payment_collection'].browse(docids)
        total_amt = 0.0
        contract_type = ''
        if docs.contract_id and docs.contract_id.parent_contract_id:
            contract_type = 'Renewal'
        else:
            contract_type = 'New'
        if docs.receipt_line_ids:
            total_amt = sum(docs.receipt_line_ids.mapped('amount'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.payment_collection',
            'docs': docs,
            'total_amt': total_amt,
            'contract_type': contract_type,
        }


class RenewalNoticeResidentialReport(models.AbstractModel):
    _name = 'report.mbk_pms.renewal_notice_residential_report'
    _description = 'Renewal Notice Residential Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.renewal_offer'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.renewal_offer',
            'docs': docs,
        }


class BreakContractReport(models.AbstractModel):
    _name = 'report.mbk_pms.break_contract_report'
    _description = 'Break Contract Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.break_contract'].browse(docids)
        sequence = []
        ascii_counter = 97
        if docs.deduction_line_ids:
            for each in docs.deduction_line_ids:
                sequence.append(chr(ascii_counter))
                ascii_counter = ascii_counter + 1
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.break_contract',
            'docs': docs,
            'sequence': sequence,
        }


class FurnitureMoveInOutReport(models.AbstractModel):
    _name = 'report.mbk_pms.furniture_move_in_out_report'
    _description = 'Furniture Move In Out Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['furniture.move'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'furniture.move',
            'docs': docs,
        }


class LeaseAgreementReport(models.AbstractModel):
    _name = 'report.mbk_pms.lease_agreement_report'
    _description = 'Lease Agreement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.contract'].browse(docids)
        annual_rent_amount = 0.0
        payment_terms = ''
        start_date = datetime.strptime(str(docs.start_date), "%Y-%m-%d")
        end_date = datetime.strptime(str(docs.expiry_date), "%Y-%m-%d") + timedelta(days=1)
        delta = relativedelta.relativedelta(end_date, start_date)
        contract_period = str(delta.years)+' Year' if delta.years > 0 else ''
        contract_period += str(delta.months) + ' Months' if delta.months > 0 else ''
        contract_period += str(delta.days) + ' Days' if delta.days > 0 else ''
        if docs.contract_type == 'extension':
            for line in docs.unit_line_ids:
                annual_rent_amount += line.annual_rent
        else:
            annual_rent_amount = docs.total_rent
        if docs.payment_terms:
            payment_terms = (docs.payment_terms).split()[0]

        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.contract',
            'docs': docs,
            'annual_rent_amount': annual_rent_amount,
            'payment_terms': payment_terms,
            'contract_period': contract_period,
        }


class GeneralApprovalReport(models.AbstractModel):
    _name = 'report.mbk_pms.general_approval_report'
    _description = 'General Approval Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['general.approval'].browse(docids)
        contract_type = ''
        if docs.contract_id and docs.contract_id.parent_contract_id:
            contract_type = 'Renewal'
        else:
            contract_type = 'New'
        return {
            'doc_ids': docs.ids,
            'doc_model': 'general.approval',
            'docs': docs,
            'contract_type':contract_type,
        }


class ChequeReleaseReport(models.AbstractModel):
    _name = 'report.mbk_pms.cheque_release_report'
    _description = 'Cheque Release Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.cheque_release'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.cheque_release',
            'docs': docs,
        }


class ChequeReplacementReport(models.AbstractModel):
    _name = 'report.mbk_pms.cheque_replacement_report'
    _description = 'Cheque Replacement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.cheque_replacement'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.cheque_release',
            'docs': docs,
        }


class ChequeHoldReport(models.AbstractModel):
    _name = 'report.mbk_pms.cheque_hold_report'
    _description = 'Cheque Hold Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mbk_pms.cheque_hold'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mbk_pms.cheque_hold',
            'docs': docs,
        }

