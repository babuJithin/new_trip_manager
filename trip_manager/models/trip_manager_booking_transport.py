# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TripManagerBookingTransport(models.Model):
    """Represents a single day's transportation record for a customer enquiry option,
    capturing vehicle selection, travel date, driver charges, and rent per day
    aligned with the tour itinerary sequence."""

    _name = 'trip.manager.booking.transport'
    _description = 'Enquiry Transportation Line'
    _order = 'day_number asc'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    day_number      = fields.Integer(string='Day')
    actual_date     = fields.Date(string='Date')
    transport_notes = fields.Text(string='Flight / Travel Notes')
    total_transport_cost = fields.Monetary(string='Day Total', compute='_compute_transport_cost', store=True, 
                                           currency_field='currency_id')
    
    tour_start_date = fields.Date(related='option_id.enquiry_id.tour_start_date', store=False)
    tour_end_date = fields.Date(related='option_id.enquiry_id.tour_end_date', store=False)
    vehicle_type = fields.Selection(related='vehicle_id.vehicle_type', readonly=True)
    rent_per_day = fields.Monetary(related='vehicle_id.rent_per_day',
                                    currency_field='currency_id', readonly=True)

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
    @api.depends('rent_per_day')
    def _compute_transport_cost(self):
        """Computes the total daily transport cost """
            
        for line in self:
            line.total_transport_cost = line.rent_per_day 
        
    @api.onchange('actual_date', 'tour_start_date')
    def _onchange_actual_date(self):
        """Derives the day number from the actual date and tour start date,
            so the transport line stays aligned with the itinerary sequence."""
            
        for rec in self:
            if rec.actual_date and rec.tour_start_date:
                rec.day_number = (rec.actual_date - rec.tour_start_date).days + 1
                
    @api.onchange('actual_date')
    def _onchange_actual_date_warning(self):
        """Shows an inline warning when the selected transport date falls
            outside the tour's start and end date range, giving the user
            immediate feedback before saving."""
            
        for rec in self:
            if rec.actual_date and rec.enquiry_id:
                if rec.actual_date < rec.enquiry_id.tour_start_date:
                    return {
                        'warning': {
                            'title': 'Invalid Date',
                            'message': 'Date cannot be before tour start date.'
                        }
                    }
                if rec.actual_date > rec.enquiry_id.tour_end_date:
                    return {
                        'warning': {
                            'title': 'Invalid Date',
                            'message': 'Date cannot be after tour end date.'
                        }
                    }