export type Language = "en" | "zh";

export interface UiMessages {
  languageName: string;
  app: {
    title: string;
    subtitle: string;
    localOnlyBadge: string;
    portableBadge: string;
    packageBadge: string;
    footer: string;
  };
  header: {
    privacy: string;
    packageStatus: string;
  };
  input: {
    title: string;
    subtitle: string;
    pasteTab: string;
    fileTab: string;
    textTitle: string;
    textLabel: string;
    textPlaceholder: string;
    fileTitle: string;
    fileLabel: string;
    filePlaceholder: string;
    helper: string;
  };
  run: {
    title: string;
    subtitle: string;
    primary: string;
    readLatest: string;
    selectedText: string;
    selectedFile: string;
    disabled: string;
  };
  status: {
    ready: string;
    preparing: string;
    running: string;
    completed: string;
    failed: string;
    readyDetail: string;
    preparingDetail: string;
    runtimePrepareFailedMessage: string;
    preparingRuntimeDetail: string;
    runtimeReadyDetail: string;
    invokingDetail: string;
    processingDetail: string;
    readingDetail: string;
    completedDetail: string;
    completedMessage: string;
    failedMessage: string;
    readFailedMessage: string;
    sampleSuccess: string;
    sampleSuccessDetail: string;
    sampleError: string;
    sampleErrorDetail: string;
    runningSummary: string;
  };
  result: {
    title: string;
    subtitle: string;
    successBanner: string;
    failureBanner: string;
    summaryTitle: string;
    requestId: string;
    status: string;
    evidenceKind: string;
    outputFiles: string;
    previewTitle: string;
    noPreview: string;
    evidenceTitle: string;
    evidenceCount: string;
    tokenFound: string;
    sourceKind: string;
    outputTitle: string;
    outputDir: string;
    outputReason: string;
    readLatest: string;
    freeLocalFact: string;
    packagedRuntimeFact: string;
    noDevWorkspaceFact: string;
    noNetworkFact: string;
  };
  supportedFormats: {
    title: string;
    subtitle: string;
    current: string;
    unsupported: string;
  };
  runtime: {
    title: string;
    subtitle: string;
    mode: string;
    localOnly: string;
    bundledAdapter: string;
    managedRuntimeAvailable: string;
    managedRuntimeSelected: string;
    selectedPython: string;
    currentPythonEnv: string;
    wheelhouseBundled: string;
    installLayoutSupported: string;
    installerBuilt: string;
    releaseCreated: string;
    cleanMachineProven: string;
    installerComplete: string;
    invokeReady: string;
    invokeE2E: string;
  };
  advanced: {
    title: string;
    subtitle: string;
    summary: string;
    devTools: string;
    sampleSuccess: string;
    sampleError: string;
    receiptTitle: string;
    receiptOutcome: string;
    receiptOutputRoot: string;
    receiptCreatedBy: string;
    usageTitle: string;
    usageKind: string;
    usageBilling: string;
    usageInputBytes: string;
    usageOutputFiles: string;
    rawUsageNote: string;
    errorTitle: string;
    noError: string;
    errorCode: string;
    errorCategory: string;
    errorMessage: string;
    errorSecretSafe: string;
    errorTechnical: string;
    lineageTitle: string;
    lineageSourceSha: string;
    lineageBaseline: string;
    proofTitle: string;
    proofSubtitle: string;
    proofExport: string;
    proofExported: string;
    proofNotExported: string;
    proofExportFailed: string;
    proofPath: string;
    proofUnavailable: string;
    proofReady: string;
    proofDone: string;
    rawJsonTitle: string;
    resultJson: string;
    receiptJson: string;
    usageJson: string;
  };
  common: {
    trueLabel: string;
    falseLabel: string;
    advancedClosed: string;
    advancedOpen: string;
    english: string;
    chinese: string;
  };
}

export const messages: Record<Language, UiMessages> = {
  en: {
    languageName: "English",
    app: {
      title: "Zephyr Base",
      subtitle: "Local document processing, private by default.",
      localOnlyBadge: "Local-only",
      portableBadge: "Portable package",
      packageBadge: "Unsigned preview",
      footer:
        "Zephyr Base remains local-only. This shell does not add PDF, DOCX, image, cloud, Pro, or billing features.",
    },
    header: {
      privacy: "Free local processing",
      packageStatus: "Unsigned portable preview",
    },
    input: {
      title: "Choose input",
      subtitle: "Paste text or point to a local text or Markdown file.",
      pasteTab: "Paste text",
      fileTab: "Local file path",
      textTitle: "Paste text",
      textLabel: "Text to process",
      textPlaceholder: "Paste local text here.",
      fileTitle: "Local file path",
      fileLabel: "File path",
      filePlaceholder: "E:/docs/example.md",
      helper: "Base supports local text and Markdown-class inputs only.",
    },
    run: {
      title: "Run",
      subtitle: "Start a local processing run and then read the generated result.",
      primary: "Run",
      readLatest: "Read latest result",
      selectedText: "Current mode: paste text",
      selectedFile: "Current mode: local file path",
      disabled: "Processing is already running.",
    },
    status: {
      ready: "Ready",
      preparing: "Preparing",
      running: "Running",
      completed: "Completed",
      failed: "Failed",
      readyDetail: "Choose a local input and start a run.",
      preparingDetail: "Preparing your local request.",
      runtimePrepareFailedMessage: "Local runtime could not be prepared.",
      preparingRuntimeDetail: "Preparing the local runtime from the packaged wheelhouse.",
      runtimeReadyDetail: "Local runtime is ready. Starting the local run.",
      invokingDetail: "Calling the desktop command bridge.",
      processingDetail: "Processing locally with the bundled adapter.",
      readingDetail: "Reading the latest local result.",
      completedDetail: "Processing complete. Your result was generated locally.",
      completedMessage: "Processing complete. Your result was generated locally.",
      failedMessage: "Processing failed. Review the friendly diagnosis below.",
      readFailedMessage: "Could not read the latest result. Review the diagnosis below.",
      sampleSuccess: "Sample success loaded",
      sampleSuccessDetail: "Regression sample loaded for UI review.",
      sampleError: "Sample error loaded",
      sampleErrorDetail: "Regression failure sample loaded for UI review.",
      runningSummary: "Current status",
    },
    result: {
      title: "View result",
      subtitle: "Read the normalized preview, result summary, and output location.",
      successBanner: "Processing complete. Your result was generated locally.",
      failureBanner: "Processing failed. Review the friendly diagnosis below.",
      summaryTitle: "Result summary",
      requestId: "Request ID",
      status: "Status",
      evidenceKind: "Evidence kind",
      outputFiles: "Output files",
      previewTitle: "Normalized preview",
      noPreview: "No normalized preview is available yet.",
      evidenceTitle: "Evidence summary",
      evidenceCount: "Elements",
      tokenFound: "Marker found",
      sourceKind: "Source kind",
      outputTitle: "Output location",
      outputDir: "Output folder",
      outputReason: "Output note",
      readLatest: "Read latest result",
      freeLocalFact: "Free local processing. No billing record is created.",
      packagedRuntimeFact: "Using the packaged local runtime.",
      noDevWorkspaceFact: "No developer workspace required.",
      noNetworkFact: "Runs without network access.",
    },
    supportedFormats: {
      title: "Supported formats",
      subtitle: "Base currently supports only local text and Markdown-class files.",
      current: "Current support",
      unsupported: "PDF, DOCX, and image inputs are not supported in this Base shell.",
    },
    runtime: {
      title: "Runtime status",
      subtitle: "Runtime truth is visible here, but the main path stays user-focused.",
      mode: "Mode",
      localOnly: "Local-only",
      bundledAdapter: "Bundled adapter",
      managedRuntimeAvailable: "Managed runtime available",
      managedRuntimeSelected: "Managed runtime selected",
      selectedPython: "Selected Python",
      currentPythonEnv: "Uses current Python environment",
      wheelhouseBundled: "Wheelhouse bundled",
      installLayoutSupported: "Install layout supported",
      installerBuilt: "Installer built",
      releaseCreated: "Release created",
      cleanMachineProven: "Clean-machine runtime proven",
      installerComplete: "Installer runtime complete",
      invokeReady: "Tauri invoke ready",
      invokeE2E: "Window click proof",
    },
    advanced: {
      title: "Advanced diagnostics",
      subtitle: "Receipt, usage facts, lineage, proof export, and regression-only tools.",
      summary: "Advanced diagnostics",
      devTools: "Developer tools",
      sampleSuccess: "Load sample success",
      sampleError: "Load sample error",
      receiptTitle: "Receipt",
      receiptOutcome: "Outcome",
      receiptOutputRoot: "Output root",
      receiptCreatedBy: "Created by",
      usageTitle: "Usage fact",
      usageKind: "Fact kind",
      usageBilling: "billing_semantics",
      usageInputBytes: "Input bytes",
      usageOutputFiles: "Output files",
      rawUsageNote: "Raw usage fact is visible here for diagnostics only.",
      errorTitle: "Error diagnosis",
      noError: "No active error.",
      errorCode: "Error code",
      errorCategory: "Category",
      errorMessage: "User message",
      errorSecretSafe: "Secret-safe",
      errorTechnical: "Technical detail",
      lineageTitle: "Lineage and runtime",
      lineageSourceSha: "Zephyr-dev source SHA",
      lineageBaseline: "Baseline reference",
      proofTitle: "Interaction proof",
      proofSubtitle:
        "Export a proof pack after a real desktop run. This remains an advanced surface.",
      proofExport: "Export interaction proof",
      proofExported: "Proof exported",
      proofNotExported: "Proof not exported",
      proofExportFailed: "Proof export failed",
      proofPath: "Proof path",
      proofUnavailable: "No real desktop run has completed yet.",
      proofReady: "Run a real local path, then export the proof pack here.",
      proofDone: "Proof exported. You can validate it with the proof checker.",
      rawJsonTitle: "Raw JSON",
      resultJson: "run_result.json",
      receiptJson: "receipt",
      usageJson: "usage_fact",
    },
    common: {
      trueLabel: "True",
      falseLabel: "False",
      advancedClosed: "Show advanced diagnostics",
      advancedOpen: "Hide advanced diagnostics",
      english: "English",
      chinese: "中文",
    },
  },
  zh: {
    languageName: "中文",
    app: {
      title: "Zephyr Base",
      subtitle: "本地文档处理，默认更重视隐私。",
      localOnlyBadge: "本地运行",
      portableBadge: "便携安装包",
      packageBadge: "未签名预览包",
      footer:
        "Zephyr Base 仍然只在本地运行。本界面不新增 PDF、DOCX、图片、云端、Pro 或计费功能。",
    },
    header: {
      privacy: "免费本地处理",
      packageStatus: "未签名便携预览包",
    },
    input: {
      title: "选择输入",
      subtitle: "粘贴文本，或填写本地文本/Markdown 文件路径。",
      pasteTab: "粘贴文本",
      fileTab: "本地文件路径",
      textTitle: "粘贴文本",
      textLabel: "待处理文本",
      textPlaceholder: "在此粘贴本地文本。",
      fileTitle: "本地文件路径",
      fileLabel: "文件路径",
      filePlaceholder: "E:/docs/example.md",
      helper: "Base 目前只支持本地文本和 Markdown 类输入。",
    },
    run: {
      title: "开始处理",
      subtitle: "启动本地处理，然后读取生成结果。",
      primary: "开始处理",
      readLatest: "读取最近结果",
      selectedText: "当前模式：粘贴文本",
      selectedFile: "当前模式：本地文件路径",
      disabled: "当前已有处理任务在运行。",
    },
    status: {
      ready: "就绪",
      preparing: "准备中",
      running: "处理中",
      completed: "已完成",
      failed: "失败",
      readyDetail: "选择本地输入后即可开始处理。",
      preparingDetail: "正在准备本地处理请求。",
      runtimePrepareFailedMessage: "本地运行时准备失败。",
      preparingRuntimeDetail: "正在从随包 wheelhouse 准备本地运行时。",
      runtimeReadyDetail: "本地运行时已就绪，正在启动本地处理。",
      invokingDetail: "正在调用桌面命令桥接层。",
      processingDetail: "正在使用随包适配器进行本地处理。",
      readingDetail: "正在读取最近一次本地结果。",
      completedDetail: "处理完成。结果已在本机生成。",
      completedMessage: "处理完成。结果已在本机生成。",
      failedMessage: "处理失败。请查看下方的友好诊断信息。",
      readFailedMessage: "读取最近结果失败。请查看下方诊断信息。",
      sampleSuccess: "已载入示例成功结果",
      sampleSuccessDetail: "已载入用于界面回归查看的示例成功结果。",
      sampleError: "已载入示例失败结果",
      sampleErrorDetail: "已载入用于界面回归查看的示例失败结果。",
      runningSummary: "当前状态",
    },
    result: {
      title: "查看结果",
      subtitle: "查看规范化预览、结果摘要和输出位置。",
      successBanner: "处理完成。结果已在本机生成。",
      failureBanner: "处理失败。请查看下方的友好诊断信息。",
      summaryTitle: "结果摘要",
      requestId: "请求 ID",
      status: "状态",
      evidenceKind: "证据类型",
      outputFiles: "输出文件数",
      previewTitle: "规范化预览",
      noPreview: "暂时没有可显示的规范化预览。",
      evidenceTitle: "证据摘要",
      evidenceCount: "元素数",
      tokenFound: "已发现标记",
      sourceKind: "来源类型",
      outputTitle: "输出位置",
      outputDir: "输出目录",
      outputReason: "输出说明",
      readLatest: "读取最近结果",
      freeLocalFact: "免费本地处理，不产生计费记录。",
      packagedRuntimeFact: "正在使用随包提供的本地运行时。",
      noDevWorkspaceFact: "不需要开发仓库。",
      noNetworkFact: "运行时不需要网络。",
    },
    supportedFormats: {
      title: "支持格式",
      subtitle: "Base 当前只支持本地文本和 Markdown 类文件。",
      current: "当前支持",
      unsupported: "当前 Base 界面不支持 PDF、DOCX 或图片输入。",
    },
    runtime: {
      title: "运行状态",
      subtitle: "这里保留运行真相信息，但主路径仍面向普通用户。",
      mode: "模式",
      localOnly: "本地运行",
      bundledAdapter: "随包适配器",
      managedRuntimeAvailable: "托管运行时可用",
      managedRuntimeSelected: "已选择托管运行时",
      selectedPython: "当前 Python",
      currentPythonEnv: "使用当前 Python 环境",
      wheelhouseBundled: "已携带 wheelhouse",
      installLayoutSupported: "支持安装布局",
      installerBuilt: "安装包已构建",
      releaseCreated: "已创建发布产物",
      cleanMachineProven: "已验证干净机器运行",
      installerComplete: "安装运行时完整",
      invokeReady: "Tauri invoke 已就绪",
      invokeE2E: "窗口点击证明",
    },
    advanced: {
      title: "高级诊断",
      subtitle: "收据、使用事实、lineage、证明导出和仅供回归的工具。",
      summary: "高级诊断",
      devTools: "开发者工具",
      sampleSuccess: "载入示例成功结果",
      sampleError: "载入示例失败结果",
      receiptTitle: "收据",
      receiptOutcome: "结果",
      receiptOutputRoot: "输出根目录",
      receiptCreatedBy: "生成方式",
      usageTitle: "使用事实",
      usageKind: "事实类型",
      usageBilling: "billing_semantics",
      usageInputBytes: "输入字节数",
      usageOutputFiles: "输出文件数",
      rawUsageNote: "这里只显示原始使用事实，供诊断使用。",
      errorTitle: "错误诊断",
      noError: "当前没有活动错误。",
      errorCode: "错误代码",
      errorCategory: "分类",
      errorMessage: "用户提示",
      errorSecretSafe: "敏感信息安全",
      errorTechnical: "技术细节",
      lineageTitle: "Lineage 与运行时",
      lineageSourceSha: "Zephyr-dev 源 SHA",
      lineageBaseline: "基线引用",
      proofTitle: "交互证明",
      proofSubtitle: "真实桌面运行后可在此导出证明包。该区域默认属于高级功能。",
      proofExport: "导出交互证明",
      proofExported: "证明已导出",
      proofNotExported: "尚未导出证明",
      proofExportFailed: "证明导出失败",
      proofPath: "证明路径",
      proofUnavailable: "尚未完成真实桌面运行。",
      proofReady: "先执行一次真实本地处理，再在这里导出证明包。",
      proofDone: "证明已导出，可使用 proof checker 验证。",
      rawJsonTitle: "原始 JSON",
      resultJson: "run_result.json",
      receiptJson: "receipt",
      usageJson: "usage_fact",
    },
    common: {
      trueLabel: "是",
      falseLabel: "否",
      advancedClosed: "展开高级诊断",
      advancedOpen: "收起高级诊断",
      english: "English",
      chinese: "中文",
    },
  },
};
