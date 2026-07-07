# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TripManagerDestination(models.Model):
    """Stores master records for travel destinations, including visiting hours,
    entry ticket details, linked hotels, cities, activities, and location categories."""
    
    _name = 'trip.manager.destination'
    _description = 'A central registry of destinations'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Name', required=True )
    image = fields.Image(string="Image", max_width=1024, max_height=1024)
    availability_type = fields.Selection([
        ('always_open', 'Open 24 Hours'),
        ('timed', 'Specific Visiting Hours')
    ], string="Availability", default='always_open')
    start_time        = fields.Float(string='Opens At')
    end_time          = fields.Float(string='Closes At')
    has_second_slot         = fields.Boolean(string='Opens Again After Break')
    slot2_start_time        = fields.Float(string='Reopens At')
    slot2_end_time          = fields.Float(string='Closes Again At')
    visiting_hours_display = fields.Char(string='Visiting Hours', compute='_compute_visiting_hours_display', 
                                         store=True)
    has_entry_ticket = fields.Boolean(string='Entry Ticket')
    entry_ticket_price = fields.Monetary(string='Entry Ticket Price', currency_field='currency_id')
    timing_display = fields.Char(compute='_compute_timing_display', store=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    hotel_ids = fields.Many2many('trip.manager.hotel', string='Hotels')
    city_ids = fields.Many2many('trip.manager.city', string='Cities')
    activity_ids = fields.Many2many('trip.manager.activity', string='Activities')
    destination_category_ids = fields.Many2many('trip.manager.destination.category', string='Location Type')
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    def _float_to_ampm(self, value):
        """Converts a float time value to a 12-hour AM/PM string format.
            For example, 13.5 becomes '1:30 PM' and 9.0 becomes '9:00 AM'."""
            
        if not value and value != 0:
            return ''
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        period = 'AM' if hours < 12 else 'PM'
        display_hour = hours % 12 or 12
        return f"{display_hour}:{minutes:02d} {period}"

    @api.depends('start_time', 'end_time', 'has_second_slot', 'slot2_start_time', 'slot2_end_time', 'availability_type')
    def _compute_visiting_hours_display(self):
        """Builds a human-readable visiting hours string based on availability type.
            For timed destinations, formats single or dual time slots in AM/PM notation.
            For non-timed destinations, displays 'Open 24 Hours'."""
            
        for rec in self:
            if rec.availability_type != 'timed':
                rec.visiting_hours_display = 'Open 24 Hours'
            elif rec.has_second_slot:
                rec.visiting_hours_display = (
                    f"{rec._float_to_ampm(rec.start_time)} – {rec._float_to_ampm(rec.end_time)}"
                    f"  |  "
                    f"{rec._float_to_ampm(rec.slot2_start_time)} – {rec._float_to_ampm(rec.slot2_end_time)}"
                )
            else:
                rec.visiting_hours_display = (
                    f"{rec._float_to_ampm(rec.start_time)} – {rec._float_to_ampm(rec.end_time)}"
                )

    @api.depends('availability_type', 'visiting_hours_display')
    def _compute_timing_display(self):
        """Resolves the final timing display label shown on the destination record.
            Delegates to visiting_hours_display for timed destinations,
            or defaults to 'Open 24 Hours' for always-open destinations."""
            
        for rec in self:
            if rec.availability_type == 'timed':
                rec.timing_display = rec.visiting_hours_display
            else:
                rec.timing_display = 'Open 24 Hours'
