---
version: "1.0.0"
last_updated: "{YYYY-MM-DD}"
categories:
  - name: "R-plotting"
    description: "R 画图相关的错误 / Errors related to R plotting"
    keywords:
      - "ggplot"
      - "ggsave"
      - "ragg"
      - "svglite"
      - "cairo"
      - "tiff"
      - "png"
      - "pdf output"
      - "axis"
      - "legend"
      - "color"
      - "fill"
      - "facet"
      - "theme"
      - "panel"
    subcategories:
      - name: "device-rendering"
        description: "渲染设备不兼容、颜色丢失、灰度输出 / Device incompatibility, color loss, greyscale output"
        examples:
          - "ggsave produced greyscale instead of color"
          - "ragg output file is corrupted"
          - "svglite text misplaced on Windows"
      - name: "color-mapping"
        description: "颜色映射错误、因子级别不匹配 / Color mapping errors, factor level mismatch"
        examples:
          - "ggplot fill colors rendered as uniform grey"
          - "color palette applied to wrong variable"
      - name: "dimension-layout"
        description: "图片尺寸、边距、标签截断 / Figure dimensions, margins, label truncation"
        examples:
          - "x-axis labels clipped at bottom"
          - "legend overlaps data area"
  - name: "R-package"
    description: "R 包安装、加载、版本冲突 / R package install, load, version conflicts"
    keywords:
      - "library"
      - "require"
      - "install.packages"
      - "BiocManager"
      - "namespace"
      - "package"
      - "version"
      - "dependency"
      - "bioconductor"
    subcategories:
      - name: "install-failure"
        description: "安装失败：镜像、编译、系统依赖 / Install failure: mirror, compilation, system dependency"
        examples:
          - "Bioconductor package requires newer R version"
          - "source compilation failed due to missing system library"
      - name: "load-conflict"
        description: "加载冲突：命名空间、函数遮蔽 / Load conflict: namespace, function masking"
        examples:
          - "dplyr::select masked by another package"
          - "namespace collision between two loaded packages"
      - name: "path-mismatch"
        description: "库路径不匹配、非标准安装位置 / Library path mismatch, non-standard install location"
        examples:
          - "package installed in user library but R looking in system library"
  - name: "python-encoding"
    description: "Python 编码、字符串、文件 I/O / Python encoding, strings, file I/O"
    keywords:
      - "encoding"
      - "decode"
      - "encode"
      - "utf-8"
      - "gbk"
      - "latin-1"
      - "unicode"
      - "chinese"
      - "write"
      - "open"
      - "csv"
      - "json.dump"
      - "chardet"
    subcategories:
      - name: "file-encoding"
        description: "读写文件时编码不兼容 / Encoding incompatibility when reading/writing files"
        examples:
          - "UTF-8 file read as GBK, Chinese characters garbled"
          - "UnicodeEncodeError when writing to file"
      - name: "stdout-encoding"
        description: "终端输出编码问题 / Terminal/stdout encoding issues"
        examples:
          - "print() fails on non-ASCII characters on Windows"
          - "subprocess output contains mojibake"
      - name: "dataframe-encoding"
        description: "DataFrame 导入导出时的编码问题 / Encoding issues with DataFrame import/export"
        examples:
          - "pandas read_csv garbled Chinese column names"
          - "to_excel corrupts special characters"
  - name: "nodejs"
    description: "Node.js 运行、模块、打包 / Node.js runtime, modules, bundling"
    keywords:
      - "npm"
      - "node"
      - "package.json"
      - "require"
      - "import"
      - "module"
      - "esm"
      - "commonjs"
      - "npx"
      - "puppeteer"
      - "chromium"
    subcategories:
      - name: "module-resolution"
        description: "模块解析失败：ESM/CJS 混用 / Module resolution failure: ESM/CJS mixing"
        examples:
          - "Cannot use import statement outside a module"
          - "require() of ES Module is not supported"
      - name: "binary-dependency"
        description: "二进制依赖：native addon 编译、Chromium 下载 / Binary dep: native addon build, Chromium download"
        examples:
          - "puppeteer chromium download failed behind proxy"
          - "node-gyp rebuild failed on Windows"
      - name: "version-mismatch"
        description: "Node/npm 版本和包的兼容性 / Node/npm version and package compatibility"
        examples:
          - "package requires Node >= 18 but running Node 16"
  - name: "shell-cli"
    description: "Shell 命令、环境变量、跨平台 / Shell commands, env vars, cross-platform"
    keywords:
      - "bash"
      - "cmd"
      - "powershell"
      - "source"
      - "export"
      - "set"
      - "PATH"
      - "which"
      - "command not found"
      - "permission denied"
      - "Rscript"
      - "segfault"
      - "cron"
      - "schtasks"
    subcategories:
      - name: "inline-execution"
        description: "内联命令执行失败 / Inline command execution failure"
        examples:
          - "Rscript -e segfaults on this platform"
          - "bash -c with complex quoting fails"
      - name: "env-var"
        description: "环境变量设置、传递 / Environment variable setting, propagation"
        examples:
          - "PATH changes in subshell not visible to parent"
          - "Windows %VAR% vs $VAR syntax confusion"
      - name: "cross-platform"
        description: "跨平台路径/分隔符/行尾 / Cross-platform path/separator/line ending"
        examples:
          - "Backslash vs forward slash in file paths"
          - "CRLF causes shell script parse error"
  - name: "obsidian"
    description: "Obsidian 专用：插件、模板、Dataview / Obsidian-specific: plugins, templates, Dataview"
    keywords:
      - "frontmatter"
      - "yaml"
      - "dataview"
      - "template"
      - "plugin"
      - "vault"
      - "wikilink"
      - "[[]]"
      - "tag"
      - "property"
    subcategories:
      - name: "frontmatter-parse"
        description: "YAML frontmatter 解析失败 / YAML frontmatter parsing failure"
        examples:
          - "Date field treated as string instead of date"
          - "Special characters in YAML breaking Dataview query"
      - name: "wikilink-resolution"
        description: "Wiki-link 解析失败、死链 / Wiki-link resolution failure, dead links"
        examples:
          - "Link to non-existent note not caught by validator"
          - "Ambiguous link target with same filename in multiple folders"
      - name: "template-expansion"
        description: "模板渲染错误 / Template expansion errors"
        examples:
          - "Templater date math producing wrong offset"
          - "Template variable not substituted"
  - name: "data-format"
    description: "数据格式：CSV、JSON、Parquet、Excel / Data formats: CSV, JSON, Parquet, Excel"
    keywords:
      - "csv"
      - "json"
      - "tsv"
      - "parquet"
      - "excel"
      - "xlsx"
      - "arrow"
      - "parse"
      - "schema"
      - "dtype"
      - "column"
    subcategories:
      - name: "type-inference"
        description: "类型推断错误：数字变成字符串等 / Type inference errors: numeric → string, etc."
        examples:
          - "Integer column with NaN values imported as float"
          - "Gene names like 'MARCH1' auto-converted to dates in Excel"
      - name: "encoding-bom"
        description: "BOM、编码检测、分隔符推断 / BOM, encoding detection, delimiter inference"
        examples:
          - "UTF-8 BOM causes first column name to be garbled"
          - "Tab-separated file misdetected as comma-separated"
      - name: "large-file"
        description: "大文件 OOM、流式处理 / Large file OOM, streaming"
        examples:
          - "pandas read_csv OOM on 5GB file"
          - "JSON file too large for json.load()"
  - name: "api-network"
    description: "API 调用、网络请求、SSL / API calls, network requests, SSL"
    keywords:
      - "api"
      - "http"
      - "https"
      - "ssl"
      - "tls"
      - "proxy"
      - "timeout"
      - "401"
      - "403"
      - "404"
      - "500"
      - "rate limit"
      - "retry"
      - "backoff"
      - "firewall"
      - "dns"
    subcategories:
      - name: "ssl-cert"
        description: "SSL 证书验证失败 / SSL certificate verification failure"
        examples:
          - "SSL certificate verify failed on corporate VPN"
          - "Self-signed certificate in internal API"
      - name: "connection-reset"
        description: "连接被重置、防火墙阻断 / Connection reset, firewall blocking"
        examples:
          - "Connection reset by peer during large download"
          - "TCP RST injected by middlebox"
      - name: "rate-limit"
        description: "速率限制、重试策略 / Rate limiting, retry strategy"
        examples:
          - "429 Too Many Requests without Retry-After header"
          - "Exponential backoff insufficient for burst limit"
      - name: "response-parsing"
        description: "响应解析错误 / Response parsing errors"
        examples:
          - "API returned HTML error page instead of JSON"
          - "Nested JSON structure changed in new API version"
  - name: "git"
    description: "Git 操作：clone、push、merge、submodule / Git operations: clone, push, merge, submodule"
    keywords:
      - "git"
      - "clone"
      - "push"
      - "pull"
      - "merge"
      - "rebase"
      - "submodule"
      - "lfs"
      - "remote"
      - "origin"
      - "branch"
      - "worktree"
    subcategories:
      - name: "protocol-blocked"
        description: "Git 协议被防火墙阻断 / Git protocol blocked by firewall"
        examples:
          - "git:// protocol blocked, must use HTTPS"
          - "SSH port 22 blocked by corporate network"
      - name: "large-file"
        description: "大文件、LFS 问题 / Large files, LFS issues"
        examples:
          - "File exceeds GitHub 100MB limit without LFS"
          - "Git LFS bandwidth quota exceeded"
      - name: "merge-conflict"
        description: "合并冲突、分支管理 / Merge conflicts, branch management"
        examples:
          - "Rebase caused repeated conflict resolution"
          - "Detached HEAD after failed submodule update"
  - name: "path-filesystem"
    description: "路径、文件系统、权限 / Path, filesystem, permissions"
    keywords:
      - "path"
      - "file"
      - "directory"
      - "permission"
      - "access denied"
      - "not found"
      - "symlink"
      - "junction"
      - "case sensitive"
      - "max path"
    subcategories:
      - name: "path-length"
        description: "路径过长 / Path too long"
        examples:
          - "Windows MAX_PATH (260 chars) exceeded in nested node_modules"
      - name: "case-sensitivity"
        description: "大小写敏感差异 / Case sensitivity differences"
        examples:
          - "File named 'Utils.ts' imported as 'utils.ts' works on macOS but fails on Linux"
      - name: "permission"
        description: "文件权限、所有权 / File permissions, ownership"
        examples:
          - "Script not executable after git clone on Linux"
          - "Windows file locked by another process"
  - name: "other"
    description: "不归入以上任何类别的错误 / Errors not fitting any above category"
    keywords:
      - "unknown"
      - "unclassified"
      - "misc"
    subcategories:
      - name: "uncategorized"
        description: "未分类的错误 / Uncategorized errors"
        examples: []
---

# 错误分类词典 / Error Taxonomy

> **注意 / Note**: 以上分类和关键词是通用模板。请根据你的实际项目替换为真实错误类型。keywords 字段是脚本做关键词预筛选的关键依据。
> The categories and keywords above are generic templates. Replace them with real error types from your projects. The `keywords` field is critical for the scanner's keyword pre-screening.

---

## 如何使用 / How to Use

### 编辑分类 / Editing Categories

1. 打开本文件的 YAML frontmatter
2. 在 `categories` 列表里添加、修改或删除条目
3. 修改 `keywords` 字段——脚本用这些词从 session 中做第一轮筛选
4. 修改 `subcategories` 和 `examples`——这些用于 LLM 聚类提示词中的 few-shot 示例

### 规则 / Rules

- **category name** 不影响自动匹配——匹配靠 `keywords`
- **keyword 应该简短**（1-3 词），不要放复杂正则——脚本做的是简单的文本包含匹配
- **每个 category 至少保留 10 个 keyword**，太少会漏报
- **subcategory 和 examples 越多越好**——它们帮助 LLM 理解分类边界

---

## 分类覆盖检查 / Category Coverage

| 分类 / Category | 子类数 / Subcats | 关键词数 / Keywords | 最后更新 / Last Updated |
|---|---|---|---|
| R-plotting | 3 | 14 | {YYYY-MM-DD} |
| R-package | 3 | 9 | {YYYY-MM-DD} |
| python-encoding | 3 | 13 | {YYYY-MM-DD} |
| nodejs | 3 | 14 | {YYYY-MM-DD} |
| shell-cli | 3 | 18 | {YYYY-MM-DD} |
| obsidian | 3 | 12 | {YYYY-MM-DD} |
| data-format | 3 | 14 | {YYYY-MM-DD} |
| api-network | 4 | 18 | {YYYY-MM-DD} |
| git | 3 | 16 | {YYYY-MM-DD} |
| path-filesystem | 3 | 15 | {YYYY-MM-DD} |
| other | 1 | 3 | {YYYY-MM-DD} |
