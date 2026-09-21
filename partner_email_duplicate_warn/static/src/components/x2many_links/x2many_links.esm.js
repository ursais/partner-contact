import { Component, usePlugin } from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";
import { ActionManagerPlugin } from "@web/webclient/actions/action_plugin";

class X2ManyLinks extends Component {
    static template = "partner_email_duplicate_warn.X2ManyLinks";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.action = usePlugin(ActionManagerPlugin);
    }

    get currentField() {
        return this.props.record.data[this.props.name];
    }

    async openFormAndDiscard(id) {
        const action = await this.orm.call(
            this.currentField.resModel,
            "action_open_business_doc",
            [id],
            {}
        );
        await this.props.record.discard();
        this.action.doAction(action);
    }
}

registry.category("fields").add("x2many_links", {
    component: X2ManyLinks,
    relatedFields: [{name: "display_name", type: "char"}],
});
