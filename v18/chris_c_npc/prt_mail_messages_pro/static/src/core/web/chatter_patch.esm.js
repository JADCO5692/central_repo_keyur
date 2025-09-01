import {Chatter} from "@mail/chatter/web_portal/chatter";
import {ChatterButtonFilter} from "@prt_mail_messages_pro/core/web/chatter_button_filter.esm";
import {patch} from "@web/core/utils/patch";

patch(Chatter, {
    components: {...Chatter.components, ChatterButtonFilter},
});

patch(Chatter.prototype, {
    async onClickFilterNotification(ev) {
        this.state.thread.displayNotifications = ev.target.checked;
        await this.state.thread.applyMessageFilter();
    },
    async onClickFilterNote(ev) {
        this.state.thread.displayNotes = ev.target.checked;
        await this.state.thread.applyMessageFilter();
    },
    async onClickFilterMessage(ev) {
        this.state.thread.displayMessages = ev.target.checked;
        await this.state.thread.applyMessageFilter();
    },

    previewMessageId: false,
});
