# Copyright 2021 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Set default Stage on partners"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env["res.partner"]
    default_stage = Partner._get_default_stage_id()
    missing_stages = Partner.search([("stage_id", "=", False)])
    if default_stage and missing_stages:
        missing_stages.write({"stage_id": default_stage.id})
