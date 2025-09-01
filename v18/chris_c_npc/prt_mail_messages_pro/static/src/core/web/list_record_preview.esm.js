import {useBus, useService} from "@web/core/utils/hooks";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";
import {ChatterPreview} from "./chatter_preview.esm";
import {session} from "@web/session";
import {Component, useState} from "@odoo/owl";

export class ListRecordPreview extends Component {
    static props = {
        ...standardWidgetProps,
    };
    setup() {
        const {Thread} = useService("mail.store");
        this.state = useState({
            threadId: false,
            threadModel: false,
            previewMessageId: false,
        });

        useBus(this.env.bus, "reload-preview", async ({detail}) => {
            if (detail !== null) {
                const {threadId, threadModel, messageId} = detail;
                if (messageId === this.state.previewMessageId) {
                    const thread = await Thread.getOrFetch({
                        model: threadModel,
                        id: threadId,
                    });
                    thread.previewMessageId = messageId;
                    this.state.threadId = threadId;
                    this.state.threadModel = threadModel;
                    this.state.previewMessageId = messageId;
                }
            }
        });
        useBus(this.env.bus, "open-record", async ({detail}) => {
            session.web_action.force_message_id = detail.resId;
            const thread = await Thread.getOrFetch({
                model: detail.data.model,
                id: detail.data.res_id.resId,
            });
            if (thread) {
                thread.previewMessageId = this.state.previewMessageId;
            }
            this.setThreadData(
                detail.data.res_id.resId,
                detail.data.model,
                detail.resId
            );
        });
        useBus(this.env.bus, "clear-chatter", () => {
            this.setThreadData();
        });
    }

    setThreadData(threadId, threadModel, previewId) {
        this.state.previewMessageId = previewId || false;
        this.state.threadId = threadId || false;
        this.state.threadModel = threadModel || false;
    }

    get className() {
        return this.props.isDisplay ? "" : "d-none";
    }
}

ListRecordPreview.template = `prt_mail_messages_pro.ListRecordPreview`;
ListRecordPreview.components = {
    ChatterPreview,
};
ListRecordPreview.props = ["isDisplay?"];
