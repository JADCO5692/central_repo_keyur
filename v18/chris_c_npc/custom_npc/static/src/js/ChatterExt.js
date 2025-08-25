/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { rpc } from "@web/core/network/rpc";
import { prettifyMessageContent } from "@mail/utils/common/format";
import { markup, toRaw, EventBus} from "@odoo/owl";

import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
export const DELAY_FOR_SPINNER = 1000;

patch(Chatter.prototype, {
    setup() {
        super.setup(...arguments);
        this.fullComposerBus = new EventBus();
    },
    async onClickFullComposer(ev){
        const newPartners = this.state.thread.suggestedRecipients.filter(
            (recipient) => recipient.checked && !recipient.persona
        );
        if (newPartners.length !== 0) {
            const recipientEmails = [];
            const recipientAdditionalValues = {};
            newPartners.forEach((recipient) => {
                recipientEmails.push(recipient.email);
                recipientAdditionalValues[recipient.email] = recipient.create_values || {};
            });
            const partners = await rpc("/mail/partner/from_email", {
                emails: recipientEmails,
                additional_values: recipientAdditionalValues,
            });
            for (const index in partners) {
                const partnerData = partners[index];
                const persona = this.store.Persona.insert({ ...partnerData, type: "partner" });
                const email = recipientEmails[index];
                const recipient = this.state.thread.suggestedRecipients.find(
                    (recipient) => recipient.email === email
                );
                Object.assign(recipient, { persona });
            }
        }
        const attachmentIds = this.props.composer.attachments?.map((attachment) => attachment.id);
        const body = this.props.composer.text;
        const validMentions = {};
        let default_body = await prettifyMessageContent(body, validMentions);
        if (!default_body) {
            const composer = toRaw(this.props.composer);
            // Reset signature when recovering an empty body.
            composer.emailAddSignature = true;
        }
        default_body = this.formatDefaultBodyForFullComposer(
            default_body,
            this.props.composer.emailAddSignature ? markup(this.store.self.signature) : ""
        );
        const context = {
            default_attachment_ids: attachmentIds,
            default_body,
            default_subject:'',
            default_email_add_signature: false,
            default_model: this.state.thread.model,
            default_partner_ids:
                this.props.type === "note"
                    ? []
                    : this.state.thread.suggestedRecipients
                          .filter((recipient) => recipient.checked)
                          .map((recipient) => recipient.persona.id),
            default_res_ids: [this.state.thread.id],
            default_subtype_xmlid: "mail.mt_comment",
            mail_post_autofollow: this.state.thread.hasWriteAccess,
        };
        const action = {
            name: this.props.type === "note" ? _t("Log note") : _t("Compose Email"),
            type: "ir.actions.act_window",
            res_model: "mail.compose.message",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: context,
        };
        const options = {
            onClose: (...args) => {
                const accidentalDiscard = args.length === 0;
                const isDiscard = accidentalDiscard || args[0]?.special;
                // otherwise message is posted (args === [undefined])
                if (!isDiscard && this.state.thread.model === "mail.box") {
                    this.notifySendFromMailbox();
                }
                if (accidentalDiscard) {
                    this.fullComposerBus.trigger("ACCIDENTAL_DISCARD", {
                        onAccidentalDiscard: (isEmpty) => {
                            if (!isEmpty) {
                                this.saveContent();
                                this.restoreContent();
                            }
                        },
                    });
                }
                this.props.messageToReplyTo?.cancel();
                this.onCloseFullComposerCallback();
                // Use another event bus so that no message is sent to the
                // closed composer.
                this.fullComposerBus = new EventBus();
            },
            props: {
                fullComposerBus: this.fullComposerBus,
            },
        };
        await this.env.services.action.doAction(action, options);
        this.state.isFullComposerOpen = true;
    },
    formatDefaultBodyForFullComposer(defaultBody, signature = "") {
        if (signature) {
            defaultBody = `${defaultBody}<br>${signature}`;
        }
        return `<div>${defaultBody}</div>`; // as to not wrap in <p> by html_sanitize
    },
    notifySendFromMailbox() {
        this.env.services.notification.add(_t('Message posted on "%s"', this.thread.displayName), {
            type: "info",
        });
    },
    saveContent() {
        const composer = toRaw(this.props.composer);
        const saveContentToLocalStorage = (text, emailAddSignature) => {
            const config = {
                emailAddSignature,
                text,
            };
            browser.localStorage.setItem(composer.localId, JSON.stringify(config));
        };
         
        this.fullComposerBus.trigger("SAVE_CONTENT", {
            onSaveContent: saveContentToLocalStorage,
        });
    },

    restoreContent() {
        const composer = toRaw(this.props.composer);
        try {
            const config = JSON.parse(browser.localStorage.getItem(composer.localId));
            if (config.text) {
                composer.emailAddSignature = config.emailAddSignature;
                composer.text = config.text;
            }
        } catch {
            browser.localStorage.removeItem(composer.localId);
        }
    },
});