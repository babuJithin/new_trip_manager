# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TripManagerFlightLine(models.Model):
    """Represents a single flight segment within a package option, capturing
    the route (from/to), flight name or number, per-passenger rate, and
    passenger count"""
    
    _name = 'trip.manager.flight.line'
    _description = 'Flight segments and airfare costing for package options'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    flight_name = fields.Char(string='Flight Name / Number')
    rate = fields.Monetary(string='Rate', currency_field='currency_id')
    no_of_pax = fields.Integer(string='No. of Pax')
    total = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_total', store=True)
    
    from_place = fields.Many2one('trip.manager.city', string='From', required=True)
    to_place = fields.Many2one('trip.manager.city', string='To', required=True)
    option_id = fields.Many2one('trip.manager.enquiry.option', string='Option', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='option_id.currency_id', store=True)

    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('rate', 'no_of_pax')
    def _compute_total(self):
        for line in self:
            line.total = line.rate * line.no_of_pax