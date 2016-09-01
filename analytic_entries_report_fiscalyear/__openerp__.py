# -*- coding: utf-8 -*-
# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Analytic Entries Statistics per fiscal period or year",
    "version": "8.0.1.0.0",
    "author": "Therp BV",
    "category": "Accounting & Finance",
    "depends": [
        'account',
    ],
    "data": [
        "views/analytics_entry_report.xml",
    ],
    "external_dependencies": {
        'python': [
            'sqlparse',
        ],
    },
}
