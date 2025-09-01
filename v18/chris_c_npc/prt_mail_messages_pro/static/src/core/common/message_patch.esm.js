import {Message} from "@mail/core/common/message";
import {_t} from "@web/core/l10n/translation";
import {parseEmail} from "@mail/utils/common/format";
import {patch} from "@web/core/utils/patch";

patch(Message.prototype, {
    setup() {
        super.setup();
        this.message.common = this;
    },

    get mailMessageType() {
        const validTypes = ["email", "email_outgoing", "comment"];
        return validTypes.includes(this.message.message_type);
    },

    get messageIsNotChannel() {
        return (
            this.message &&
            !this.deletable &&
            this.mailMessageType &&
            this.message.thread.model !== "discuss.channel"
        );
    },

    get isAuthored() {
        return Boolean(this.message.author);
    },

    openRecord() {
        if (this.message.displayDocumentLink) {
            const {model, id} = this.message.thread;
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: model,
                res_id: id,
                views: [[false, "form"]],
                target: "current",
            });
        } else {
            super.openRecord(...arguments);
        }
    },

    get isPreviewMessage() {
        return this.message.id === this.props.thread.previewMessageId;
    },

    async refreshThreadMessage() {
        this.props.thread.isLoaded = false;
        await Promise.all([
            this.props.thread.fetchNewMessages(),
            this.message.thread.fetchNewMessages(),
        ]);
        this.env.bus.trigger("reload-preview");
    },

    async openReplyAction(mode) {
        const context = await this.env.services.orm.call(
            "mail.message",
            "reply_prep_context",
            [[this.message.id]],
            {context: {wizard_mode: mode}}
        );
        return this.env.services.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "mail.compose.message",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context: context,
            },
            {
                onClose: () => this.refreshThreadMessage(),
            }
        );
    },

    async openReplyForwardMessage() {
        return this.openReplyAction("forward");
    },

    async openReplyQuoteMessage() {
        return this.openReplyAction("quote");
    },

    async openMoveMessage() {
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "prt.message.move.wiz",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context: {
                    thread_message_id: this.message.id,
                },
            },
            {
                onClose: () => this.refreshThreadMessage(),
            }
        );
    },

    async openEditMessage() {
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "cx.message.edit.wiz",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context: {
                    active_ids: [this.message.id],
                },
            },
            {
                onClose: () => this.refreshThreadMessage(),
            }
        );
    },

    async openAssignAuthor() {
        const [name, email] = this.message.email_from
            ? parseEmail(this.message.email_from)
            : [null, null];
        this.action.doAction(
            {
                name: _t("Assign Author"),
                type: "ir.actions.act_window",
                res_model: "cx.message.partner.assign.wiz",
                views: [[false, "form"]],
                target: "new",
                context: {
                    default_name: name,
                    default_email: email,
                    active_id: this.message.id,
                },
            },
            {
                onClose: () => this.refreshThreadMessage(),
            }
        );
    },
});
