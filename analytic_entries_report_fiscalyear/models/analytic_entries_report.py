# -*- coding: utf-8 -*-
# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, models, fields


class AnalyticEntriesReport(models.Model):
    _inherit = 'analytic.entries.report'

    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal year')
    period_id = fields.Many2one('account.period', 'Fiscal period')

    def init(self, cr):
        # mutatis mutandis the same query as in
        # account_analytic_entries_report.py
        # added joins to account_period & account_move_line
        # added appropriate fields to select list and group by
        cr.execute("""
            create or replace view analytic_entries_report as (
                 select
                     min(a.id) as id,
                     count(distinct a.id) as nbr,
                     a.date as date,
                     a.user_id as user_id,
                     a.name as name,
                     analytic.partner_id as partner_id,
                     a.company_id as company_id,
                     a.currency_id as currency_id,
                     a.account_id as account_id,
                     a.general_account_id as general_account_id,
                     a.journal_id as journal_id,
                     a.move_id as move_id,
                     a.product_id as product_id,
                     a.product_uom_id as product_uom_id,
                     sum(a.amount) as amount,
                     sum(a.unit_amount) as unit_amount,
                     coalesce(ml.period_id, p.id) as period_id,
                     coalesce(p_from_move.fiscalyear_id, p.fiscalyear_id)
                        as fiscalyear_id

                 from
                     account_analytic_line a
                     join account_analytic_account analytic
                        on analytic.id = a.account_id
                     left outer join account_period p
                        on p.special = False and p.date_start <= a.date
                            and p.date_stop >= a.date
                     left outer join account_move_line ml
                        on a.move_id = ml.id
                     left outer join account_period p_from_move
                        on ml.period_id = p_from_move.id

                 group by
                     a.date,
                     coalesce(p_from_move.fiscalyear_id, p.fiscalyear_id),
                     coalesce(ml.period_id, p.id), a.user_id,a.name,
                     analytic.partner_id,a.company_id, a.currency_id,
                     a.account_id,a.general_account_id,a.journal_id,
                     a.move_id,a.product_id,a.product_uom_id
            )
        """)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        '''Override read_group to respect filters whose domain can't be
        computed on the client side'''
        adjusted_domain = []

        for proposition in domain:
            if not isinstance(proposition, tuple) and\
                    not isinstance(proposition, list) or\
                    len(proposition) != 3:
                # we can't use expression.is_leaf here because of our custom
                # operator
                adjusted_domain.append(proposition)
                continue
            field, operator, value = proposition
            if field == 'fiscalyear_id' and operator == 'offset':
                date = datetime.date.today() + relativedelta(years=value)
                fiscalyear_id = self.env['account.fiscalyear'].find(dt=date)
                adjusted_domain.append(('fiscalyear_id', '=', fiscalyear_id))
            elif field == 'period_id' and operator == 'offset':
                current_period = self.env['account.period'].with_context(
                    account_period_prefer_normal=True).find()

                direction = '>='
                if value < 0:
                    direction = '<='

                periods = current_period.search(
                    [
                        ('date_start', direction, current_period.date_start),
                        ('special', '=', False),
                    ], limit=(abs(value) + 1) or 1, order='date_start ' +
                    ('asc' if direction == '>=' else 'desc')
                )

                adjusted_domain.append(('period_id', '=', periods[value].id))
            else:
                adjusted_domain.append(proposition)

        return super(AnalyticEntriesReport, self).read_group(
            adjusted_domain, fields, groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy)
