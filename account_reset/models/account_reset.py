# -*- coding: utf-8 -*-

##############################################################################
#
# Accounts Reset
# Copyright (C) 2016 OpusVL (<http://opusvl.com/>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp.exceptions import Warning, AccessError
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

class AccountResetWizard(models.Model):
    _name = 'account.reset.wizard'

    company_id = fields.Many2one(string="Which company?", comodel_name="res.company", required=True, help='Choose the company whose accounts you wish to reset')
    confirmed = fields.Boolean(string='I understand the implications of this, and that this action may be logged.  I have checked that the chosen company is correct.', required=True)
    executed = fields.Boolean(string="Successfully executed")

    uncancellable_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        compute="_compute_uncancellable_journals",
        readonly=True,
    )
    have_uncancellable_journals = fields.Boolean(compute='_compute_uncancellable_journals')

    @api.depends('company_id')
    @api.one
    def _compute_uncancellable_journals(self):
        if self.company_id:
            self.uncancellable_journal_ids = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('update_posted', '=', False),
            ])
        else:
            self.uncancellable_journal_ids = self.env['account.journal']
        self.have_uncancellable_journals = bool(self.uncancellable_journal_ids)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.confirmed = False

    @api.one
    def execute(self):
        company = self.company_id
        log_data = {
            'reset_id': self.id,
            'login': self.env.user.login,
            'company_name': company.name if company else '*unset*'
        }
        if not self.env.user.has_group('account_reset.group_allow_account_reset'):
            _logger.warn("User '{login}' tried but does not have permission to reset accounts for '{company_name}'.  Add them to the Account Reset group if they should.".format(**log_data))
            raise AccessError(_("You do not have permission to reset the accounts"))
        if self.executed:
            raise Warning(_("Wizard record already executed"))
        if not self.company_id:
            raise Warning(_("Cannot reset accounts: You did not choose a company for whom the chart of accounts should be reset"))
        if not self.confirmed:
            raise Warning(_("Cannot reset accounts: You did not tick the confirmation box"))

        log_data['prefix'] = "account reset {reset_id}:".format(**log_data)
        _logger.info("{prefix} started by: '{login}', company: {company_name}".format(**log_data))
        self_log = self.with_context(log_data=log_data)
        self_log._unpost_journal_entries()
        self_log._unpost_invoices()
        self_log._unpost_vouchers()
        _logger.info('{prefix} finished'.format(**log_data))
        self.executed = True

    def _unpost_journal_entries(self):
        self.ensure_one()
        company = self.company_id
        log_data = self.env.context['log_data'].copy()
        journal_entries = self.env['account.move'].search([('state', '=', 'posted'), ('company_id', '=', company.id)])
        _logger.info('{prefix} {count} Posted journal entries to cancel'.format(
            count=len(journal_entries), **log_data))
        for entry in journal_entries:
            entry_log_data = log_data.copy()
            entry_log_data.update(dict(entry_id=entry.id, entry_name=entry.name))
            if entry.journal_id.update_posted:
                _logger.info('{prefix} Cancelling journal entry {entry_id} "{entry_name}"'.format(**entry_log_data))
                entry.button_cancel()
            else:
                _logger.warn('{prefix} Skipping Journal entry {entry_id} "{entry_name}" - it is in uncancellable journal {journal_name}'.format(journal_name=entry.journal_id.name, **entry_log_data))

    def _unpost_invoices(self):
        self.ensure_one()
        company = self.company_id
        log_data = self.env.context['log_data'].copy()
        invoices = self.env['account.invoice'].search([('state', 'in', ['open', 'paid']), ('company_id', '=', company.id)])
        _logger.info('{prefix} {count} invoices to cancel'.format(
            count=len(invoices), **log_data
        ))
        for invoice in invoices:
            inv_log_data = log_data.copy()
            inv_log_data.update(dict(invoice_name=invoice.name or "*no name*", invoice_id=invoice.id))
            journal = invoice.journal_id
            if not journal.update_posted:
                _logger.info('{prefix} Skipping Invoice {invoice_id} "{invoice_name}" - it is in uncancellable journal {journal_name}'.format(journal_name=journal.name, **inv_log_data))
                continue
            _logger.info('{prefix} cancelling invoice {invoice_id} "{invoice_name}"'.format(**inv_log_data))
            invoice.signal_workflow('invoice_cancel')

    def _unpost_vouchers(self):
        self.ensure_one()
        company = self.company_id
        log_data = self.env.context['log_data'].copy()
        try:
            AccountVoucher = self.env['account.voucher']
        except KeyError:
            _logger.warning("{prefix} account.voucher model not present - skipping voucher cancellation".format(**log_data))
            return
        vouchers = AccountVoucher.search([('state', '=', 'posted'), ('company_id', '=', company.id)])
        _logger.info('{prefix} {count} vouchers to cancel'.format(
            count=len(vouchers), **log_data
        ))
        for voucher in vouchers:
            inv_log_data = log_data.copy()
            inv_log_data.update(dict(voucher_name=voucher.display_name or "*no name*", voucher_id=voucher.id))
            journal = voucher.journal_id
            if not journal.update_posted:
                _logger.info('{prefix} Skipping Voucher {voucher_id} "{voucher_name}" - it is in uncancellable journal {journal_name}'.format(journal_name=journal.name, **inv_log_data))
                continue
            _logger.info('{prefix} cancelling voucher {voucher_id} "{voucher_name}"'.format(**inv_log_data))
            voucher.cancel_voucher()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
