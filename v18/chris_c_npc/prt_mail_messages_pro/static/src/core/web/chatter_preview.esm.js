import {onMounted, onWillUpdateProps} from "@odoo/owl";
import {Chatter} from "@mail/chatter/web_portal/chatter";

export class ChatterPreview extends Chatter {
    static template = "prt_mail_messages_pro.ChatterPreview";
    setup() {
        super.setup();
        onMounted(() => {
            this.changeThread(
                this.props.threadModel,
                this.props.threadId,
                this.props.webRecord
            );
            if (!this.env.chatter || this.env.chatter?.fetchData) {
                if (this.env.chatter) {
                    this.env.chatter.fetchData = false;
                }
                this.state.thread.previewMessageId = this.props.previewMessageId;
                this.load(this.state.thread, ["messages"]);
            }
        });

        onWillUpdateProps((nextProps) => {
            if (
                this.props.threadId !== nextProps.threadId ||
                this.props.threadModel !== nextProps.threadModel
            ) {
                this.props.has_activities = false;
                this.changeThread(
                    nextProps.threadModel,
                    nextProps.threadId,
                    nextProps.webRecord
                );
            }
            this.state.thread.previewMessageId = nextProps.previewMessageId;
            if (!this.env.chatter || this.env.chatter?.fetchData) {
                if (this.env.chatter) {
                    this.env.chatter.fetchData = false;
                }
                this.load(this.state.thread, ["messages"]);
            }
        });
    }
}
ChatterPreview.props = [...ChatterPreview.props, "previewMessageId?"];
