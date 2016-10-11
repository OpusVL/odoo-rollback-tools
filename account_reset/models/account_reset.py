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


    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.confirmed = False

    @api.one
    def execute(self):
        company = self.company_id
        log_data = {
            'reset_id': self.id,
            'login': self.env.user.login,
            'company': company.name if company else '*unset*'
        }
        if not self.env.user.has_group('account_reset.group_allow_account_reset'):
            _logger.warn("User '{login}' tried but does not have permission to reset accounts for '{company}'.  Add them to the Account Reset group if they should.".format(**log_data))
            raise AccessError(_("You do not have permission to reset the accounts"))
        if self.executed:
            raise Warning(_("Wizard record already executed"))
        if not self.company_id:
            raise Warning(_("Cannot reset accounts: You did not choose a company for whom the chart of accounts should be reset"))
        if not self.confirmed:
            raise Warning(_("Cannot reset accounts: You did not tick the confirmation box"))

        _logger.info("account reset {reset_id}: started by: '{login}', company: {company}".format(**log_data))
        self.with_context(log_data=log_data)._reset_company_accounts(company)
        _logger.info('account reset {reset_id}: finished'.format(**log_data))
        self.executed = True

    def _reset_company_accounts(self, company):
        self.ensure_one()
        log_data = self.env.context['log_data'].copy()
        log_data['company_name'] = company.name
        for_company = [('company_id', '=', company.id)]
        #posted_journal_entries = self.env['account.journal.entry'].search([('')])
        journal_entries = self.env['account.move'].search([('state', '=', 'posted')] + for_company)
        _logger.info('account reset {reset_id}: {company_name}: {count} Posted journal entries to cancel'.format(
            count=len(journal_entries), **log_data))
        for entry in journal_entries:
            entry_log_data = log_data.copy()
            entry_log_data.update(dict(entry_id=entry.id, entry_name=entry.name))
            if entry.journal_id.update_posted:
                _logger.info('account reset {reset_id}: {company_name}: Cancelling journal entry {entry_id} "{entry_name}"'.format(**entry_log_data))
                entry.button_cancel()
            else:
                _logger.warn('account reset {reset_id}: {company_name}: Skipping Journal entry {entry_id} "{entry_name}" is in uncancellable journal {journal_name}'.format(journal_name=entry.journal_id.name, **entry_log_data))



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
