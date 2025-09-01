import {MailMessageUpdateListController} from "@prt_mail_messages/views/list/mail_message_list_controller.esm";
import {session} from "@web/session";
import {useBus} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";

export class MailMessagePreviewListController extends MailMessageUpdateListController {
    setup() {
        super.setup();
        this.state = useState({
            previewMode: true,
        });
        session.web_action = {
            action_id: this.env.config.actionId,
        };
        useBus(this.env.bus, "reload-preview", () => {
            this.model.load();
        });
        useBus(this.env.bus, "mail.message/delete", () => {
            this.model.load();
        });
    }

    get className() {
        if (this.state.previewMode) {
            return super.className + " preview-mode";
        }
        return super.className;
    }

    get getPreviewClass() {
        if (this.state.previewMode) {
            return "fa fa-eye";
        }
        return "fa fa-eye-slash";
    }

    async openRecord(record, force = false) {
        if (this.state.previewMode) {
            this.env.bus.trigger("open-record", record);
        } else {
            super.openRecord(record, force);
        }
    }

    onSwitchPreview(event) {
        this.state.previewMode = !this.state.previewMode;
        event.target.blur();
        if (!this.state.previewMode) {
            this.env.bus.trigger("clear-chatter");
        }
        globalThis.dispatchEvent(new globalThis.Event("resize"));
    }
}

MailMessagePreviewListController.template = "prt_mail_messages_pro.MessageListView";
