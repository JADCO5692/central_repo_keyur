import {Thread} from "@mail/core/common/thread_model";
import {session} from "@web/session";
import {patch} from "@web/core/utils/patch";

patch(Thread.prototype, {
    async setDefaultThreadFilters() {
        this.displayNotifications = true;
        this.displayNotes = true;
        this.displayMessages = true;
    },

    getFetchParams() {
        const params = super.getFetchParams(...arguments);
        if (this.fetchAllMessages) {
            this.previewMessageId = false;
            this.fetchAllMessages = false;
        }
        if (this.previewMessageId) {
            return {
                ...params,
                action_id: session.web_action.action_id,
                force_message_id: this.previewMessageId,
            };
        }
        return params;
    },

    async applyMessageFilter() {
        let filteredMessage = [...this.allMessages];
        if (!this.displayNotifications) {
            filteredMessage = filteredMessage.filter(
                (msg) => !msg.is_notification && msg.type !== "notification"
            );
        }
        if (!this.displayNotes) {
            filteredMessage = filteredMessage.filter((msg) => !msg.is_note);
        }
        if (!this.displayMessages) {
            filteredMessage = filteredMessage.filter((msg) => !msg.is_discussion);
        }
        this.messages = filteredMessage;
    },

    get nonEmptyMessages() {
        if (this.previewMessageId) {
            return [...this.messages].filter(
                (message) => message.id === this.previewMessageId
            );
        }
        return super.nonEmptyMessages;
    },

    displayNotifications: true,
    displayNotes: true,
    displayMessages: true,
    previewMessageId: false,
    fetchAllMessages: false,
});
