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


{
    'name': 'Accounts Reset',
    'version': '0.1',
    'author': 'OpusVL',
    'website': 'http://opusvl.com/',
    'summary': 'Automatically reset accounts ready for transition to live, for example',
    
    'category': 'Technical',
    
    'description': """Automatically reset accounts ready for transition to live, for example.

    Once this module is installed, you need to grant permissions to those who are going to perform the accounts reset.
    I suggest that once the user has done what they need with it, you then revoke those permissions.

    The permission in question is 'Accounts reset'.  The user will also need the permissions that would normally
    be necessary to unreconcile invoices, vouchers and journal entires manually (probably Accounting Manager).

    There will be a new menu entry Accounting -> Configuration -> Reset Accounts.

    Click that, and pick the company whose accounts you wish to reset.

    When you select a company, you may get a warning about certain journals having unreconciliation disabled.
    If any journals whose postings you don't wish to preserve are in this list, then you will need to go to the journal
    and tick the box to allow unreconciliation of entries.

    Once you are happy with your choices, you will need to tick the checkbox, and note that your request will be logged.

    Click the 'Reset Accounts' button.  Note that this operation, especially the voucher cancellation stage, is quite slow.
""",
    'images': [
    ],
    'depends': [
        'account',
        'account_cancel',
    ],
    'data': [
        'security/groups.xml',
        'views/account_reset.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
