# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


CATEGORY_STAR_MAP = {
    'standard': ['1', '2'],
    'deluxe': ['3'],
    'premium': ['4'],
    'luxury': ['5'],
}

class TripManagerHotel(models.Model):
    """Stores master records for hotels across travel destinations and cities,
    capturing contact details, address, star rating, room types, check-in/check-out
    times, breakfast availability, extra bed pricing, and serviceable cities
    used for filtering hotels by destination and package category tier."""
    
    _name = 'trip.manager.hotel'
    _description = 'A central registry of hotels'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Hotel Name', required=True )
    image = fields.Image(string="Image", max_width=1024, max_height=1024)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    email = fields.Char(string='Email', required=True)
    phone_number = fields.Char(string='Phone Number', required=True)
    star_rating = fields.Selection([
        ('0', '0 star'),
        ('1', '1 star'),
        ('2', '2 star'),
        ('3', '3 star'),
        ('4', '4 star'),
        ('5', '5 star'),
    ], string='Star Rating')
    check_in = fields.Float(string='Check-in Time')
    check_out = fields.Float(string='Check-out Time')
             
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)   
    city_ids = fields.Many2many('trip.manager.city', string='Cities')
    room_type_ids = fields.One2many('trip.manager.hotel.room.type', 'hotel_id', string="Room Types")
    
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    def _float_to_ampm(self, value):
        """Converts a float time value to a 12-hour AM/PM string format.
        For example, 14.5 becomes '2:30 PM' and 9.0 becomes '9:00 AM'."""
        
        if not value and value != 0:
            return ''
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        period = 'AM' if hours < 12 else 'PM'
        display_hour = hours % 12 or 12
        return f"{display_hour}:{minutes:02d} {period}"
    
    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Orders dropdown results so hotels matching the enquiry option's
        package category star tier appear first, then higher-tier hotels
        in ascending order (upgrades), then lower-tier hotels in
        descending order (nearest downgrade first)."""

        category = self.env.context.get('preferred_stars')
        stars = CATEGORY_STAR_MAP.get(category)
        if not stars:
            return super().name_search(name=name, domain=domain, operator=operator, limit=limit)
        domain = domain or []
        name_domain = [('name', operator, name)] if name else []
        preferred = self.search(domain + name_domain
                                + [('star_rating', 'in', stars)],
                                order='star_rating asc, name asc')

        top_tier = int(max(stars))
        rest = self.search(domain + name_domain
                           + [('id', 'not in', preferred.ids)])
        rest = rest.sorted(key=lambda h: (
            0 if int(h.star_rating or 0) > top_tier else 1,
            int(h.star_rating or 0) if int(h.star_rating or 0) > top_tier
            else -int(h.star_rating or 0),
            h.name or ''
        ))
        records = (preferred + rest)[:limit]
        return [(rec.id, rec.display_name) for rec in records]
    
    @api.depends('name', 'star_rating')
    def _compute_display_name(self):
        """Overrides display name to prefix the hotel name with star emoji icons
        based on the star rating, improving readability in dropdown selections.
        For example, a 3-star hotel displays as '⭐⭐⭐ Hotel Name'."""
        
        star_display = {
            '0': '☆ ',
            '1': '⭐',
            '2': '⭐⭐',
            '3': '⭐⭐⭐',
            '4': '⭐⭐⭐⭐',
            '5': '⭐⭐⭐⭐⭐',
        }
        for rec in self:
            stars = star_display.get(rec.star_rating, '')
            rec.display_name = f"{stars} {rec.name}"

    @api.onchange('state_id')
    def _onchange_state_id(self):
        """Auto-fills country when a state is selected."""
        
        if self.state_id:
            self.country_id = self.state_id.country_id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clears state if it does not belong to the selected country."""
        
        if self.state_id and self.state_id.country_id != self.country_id:
            self.state_id = False