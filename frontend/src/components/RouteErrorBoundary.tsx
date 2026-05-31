import { Component, type ErrorInfo, type ReactNode } from "react";

import { fetchClientMeta, type ClientMetaResponse } from "../api/client";

type Props = { children: ReactNode };
type State = { hasError: boolean; message: string };

export default class RouteErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(): State {
    return { hasError: true, message: "" };
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    fetchClientMeta()
      .then((meta: ClientMetaResponse) => {
        this.setState({
          hasError: true,
          message: meta.fatal_ui_error || error.message,
        });
      })
      .catch(() => {
        this.setState({ hasError: true, message: error.message });
      });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="meta-loading" role="alert">
          <p>{this.state.message || "页面发生错误，请刷新后重试"}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
