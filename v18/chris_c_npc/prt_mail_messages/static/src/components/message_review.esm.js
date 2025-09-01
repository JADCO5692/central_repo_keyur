import {Component, onWillStart, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";

export class MessageReview extends Component {
    static template = "prt_mail_messages.MessageReview";
    static props = ["record", "note_color"];

    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            record: this.props.record.data,
            resId: this.props.record.resId,
            attachments: [],
            has_attachments: this.props.record.data.attachment_ids.resIds.length > 0,
        });
        onWillStart(this.onWillStart);
    }

    async onWillStart() {
        const attachmentIds = this.state.record.attachment_ids.resIds;
        if (attachmentIds.length > 0) {
            this.state.attachments = await this.orm.call("ir.attachment", "read", [
                attachmentIds,
                ["name"],
            ]);
        }
    }

    get table_class() {
        if (this.state.record.is_note) {
            let color = null;
            // eslint-disable-next-line no-undef
            if (window.CSS === undefined) {
                color = this.props.note_color;
            } else {
                // eslint-disable-next-line no-undef
                color = CSS.escape(this.props.note_color);
            }
            return `background-color: ${color}`;
        }
        return "";
    }

    get title() {
        if (this.state.record.is_note) {
            return _t("Internal Note");
        }
        return _t("Message");
    }

    get avatar() {
        if (this.state.record.author_avatar) {
            return `/web/image/mail.message/${encodeURIComponent(this.state.resId)}/author_avatar`;
        }
        return "/web/static/img/user_placeholder.jpg";
    }

    get delete_date() {
        if (this.state.record.deleted_days === 0) {
            return _t("Deleted less than one day ago");
        }
        return _t(`Deleted ${this.state.record.deleted_days} days ago`);
    }

    get attachments() {
        const filenames = this.state.attachments.map((a) => a.name);
        return filenames.join("\r");
    }

    openRecordReference(ev) {
        ev.stopPropagation();
        const recordRef = this.state.record.record_ref;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            views: [[false, "form"]],
            res_model: recordRef.resModel,
            res_id: recordRef.resId,
        });
    }
}
