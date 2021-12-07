# Copyright 2019 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["confirmed"]
    _tier_validation_manual_config = False

    state = fields.Selection(related="stage_id.state")

    @api.model
    def _tier_revalidation_fields(self):
        """
        Changing some Partner fields forces Tier Validation to be reevaluated.
        Out of the box these are is_company and parent_id.
        Other can be added extenting this method.
        """
        return ["is_company", "parent_id"]

    def write(self, vals):
        # Changing certain fields required new validation process
        revalidate_fields = self._tier_revalidation_fields()
        if any(x in revalidate_fields for x in vals.keys()):
            self.mapped("review_ids").unlink()
            PartnerStage = self.env["res.partner.stage"]
            draft_stage = PartnerStage.search([("state", "=", "draft")], limit=1)
            vals["stage_id"] = draft_stage.id
        return super().write(vals)
