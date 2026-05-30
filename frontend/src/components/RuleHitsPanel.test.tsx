import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { RuleHitRecord } from "../api/client";
import RuleHitsPanel from "./RuleHitsPanel";

const headers = ["规则 ID", "严重级别", "文件", "证据摘要", "规则说明"];

const sampleHits: RuleHitRecord[] = [
  {
    rule_id: "hardcoded-secret",
    severity: "HIGH",
    file_path: "app/config.py",
    evidence: "password = '123'",
    message: "禁止硬编码密钥",
  },
  {
    rule_id: "hardcoded-secret",
    severity: "HIGH",
    file_path: "app/auth.py",
    evidence: "api_key = 'abc'",
    message: "禁止硬编码密钥",
  },
  {
    rule_id: "bare-except",
    severity: "LOW",
    file_path: "app/main.py",
    evidence: "except:",
    message: "避免裸 except",
  },
];

const defaultProps = {
  headers,
  emptyText: "无规则命中。",
  groupByRuleIdLabel: "按规则分组",
  collapseLowLabel: "折叠 LOW",
  hitCountLabel: "命中 {count} 次",
};

describe("RuleHitsPanel", () => {
  afterEach(() => {
    cleanup();
  });

  it("无命中时展示空态文案", () => {
    render(<RuleHitsPanel hits={[]} {...defaultProps} />);
    expect(screen.getByText("无规则命中。")).toBeInTheDocument();
  });

  it("渲染表头与 message 列", () => {
    render(<RuleHitsPanel hits={sampleHits} {...defaultProps} groupByRuleIdDefault={false} />);
    expect(screen.getByText("规则说明")).toBeInTheDocument();
    expect(screen.getAllByText("禁止硬编码密钥").length).toBe(2);
    expect(screen.getByText("避免裸 except")).toBeInTheDocument();
  });

  it("按严重级别筛选", () => {
    render(<RuleHitsPanel hits={sampleHits} {...defaultProps} groupByRuleIdDefault={false} />);
    fireEvent.click(screen.getByRole("button", { name: "LOW" }));
    expect(screen.queryByText("禁止硬编码密钥")).not.toBeInTheDocument();
    expect(screen.getByText("避免裸 except")).toBeInTheDocument();
  });

  it("折叠 LOW 时隐藏低严重级别命中", () => {
    render(<RuleHitsPanel hits={sampleHits} {...defaultProps} groupByRuleIdDefault={false} />);
    fireEvent.click(screen.getByLabelText("折叠 LOW"));
    expect(screen.queryByText("避免裸 except")).not.toBeInTheDocument();
    expect(screen.getAllByText("禁止硬编码密钥").length).toBeGreaterThan(0);
  });

  it("按规则分组时展示分组标题与命中次数", () => {
    render(<RuleHitsPanel hits={sampleHits} {...defaultProps} groupByRuleIdDefault />);
    expect(screen.getByText(/hardcoded-secret · HIGH · 命中 2 次/)).toBeInTheDocument();
    expect(screen.getByText(/bare-except · LOW · 命中 1 次/)).toBeInTheDocument();
  });

  it("取消分组后按行平铺展示", () => {
    render(<RuleHitsPanel hits={sampleHits} {...defaultProps} groupByRuleIdDefault />);
    fireEvent.click(screen.getByLabelText("按规则分组"));
    expect(screen.queryByText(/命中 2 次/)).not.toBeInTheDocument();
    expect(screen.getAllByRole("row").length).toBeGreaterThan(3);
  });
});
