# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class TripManagerBookingTransport(models.Model):
    """Represents a single day's transportation record for a customer enquiry option,
    capturing vehicle selection, travel date, driver charges, and rent per day
    aligned with the tour itinerary sequence."""

    _name = 'trip.manager.booking.transport'
    _description = 'Enquiry Transportation Line'
    _order = 'actual_date asc'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    day_number      = fields.Integer(string='Day')
    actual_date = fields.Date(string='Date', default=lambda self: self._default_actual_date())
    transport_notes = fields.Text(string='Flight / Travel Notes')
    total_transport_cost = fields.Monetary(string='Day Total', compute='_compute_transport_cost', store=True, 
                                           currency_field='currency_id')
    
    tour_start_date = fields.Date(related='option_id.enquiry_id.tour_start_date', store=False)
    tour_end_date = fields.Date(related='option_id.enquiry_id.tour_end_date', store=False)
    vehicle_type = fields.Selection(related='vehicle_id.vehicle_type', readonly=True)
    rent_per_day = fields.Monetary(string='Rent / Day', compute='_compute_rent_per_day', store=True, 
                                   readonly=False, currency_field='currency_id')

    package_id = fields.Many2one(related='enquiry_id.package_id', store=True)
    itineary_id = fields.Many2one('trip.manager.itineary', string='Itinerary Day',
                                  domain="[('package_id', '=', package_id)]")
    vehicle_id = fields.Many2one('trip.manager.vehicle', string='Vehicle')
    currency_id = fields.Many2one('res.currency', related='option_id.currency_id', string="Currency")
    option_id  = fields.Many2one('trip.manager.enquiry.option', required=True, ondelete='cascade')
    enquiry_id = fields.Many2one('trip.manager.enquiry',related='option_id.enquiry_id', 
                                 store=True, string='Enquiry')
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.depends('vehicle_id')
    def _compute_rent_per_day(self):
        """Seeds the rent from the selected vehicle's master rate.
        and the user can override it per-line without affecting the 
        vehicle master record"""
        
        for line in self:
            line.rent_per_day = line.vehicle_id.rent_per_day
            
    @api.depends('rent_per_day')
    def _compute_transport_cost(self):
        """Computes the total daily transport cost """
            
        for line in self:
            line.total_transport_cost = line.rent_per_day 
            
    def _default_actual_date(self):
        """Defaults the transport date to the tour start date so the
        datepicker opens within the tour period."""

        option_id = self.env.context.get('default_option_id')
        if option_id:
            option = self.env['trip.manager.enquiry.option'].browse(option_id)
            return option.enquiry_id.tour_start_date
        return False
        
    @api.onchange('actual_date', 'tour_start_date')
    def _onchange_actual_date(self):
        """Derives the day number from the actual date, warns and resets
        the date when it falls outside the tour's date range."""

        for rec in self:
            if not rec.actual_date:
                continue

            start = rec.tour_start_date or self.env.context.get('tour_start_date')
            end = rec.tour_end_date or self.env.context.get('tour_end_date')
            if start and isinstance(start, str):
                start = fields.Date.from_string(start)
            if end and isinstance(end, str):
                end = fields.Date.from_string(end)

            if start and rec.actual_date < start:
                rec.actual_date = start 
                rec.day_number = 1
                return {
                    'warning': {
                        'title': 'Invalid Date',
                        'message': 'Date cannot be before the tour start date (%s)' % start
                    }
                }
            if end and rec.actual_date > end:
                rec.actual_date = end or False 
                rec.day_number = 1 if start else 0
                return {
                    'warning': {
                        'title': 'Invalid Date',
                        'message': 'Date cannot be after the tour end date (%s)' % end
                    }
                }

            if start:
                rec.day_number = (rec.actual_date - start).days + 1