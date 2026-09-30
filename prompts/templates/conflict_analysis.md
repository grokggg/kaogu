### 【材料冲突】

{{#if no_conflicts}}
本次材料之间未发现直接矛盾。
{{else}}
{{#each conflicts}}
#### 冲突：关于{{topic}}
| 版本 | 内容 | 来源 | 优先级 |
|------|------|------|--------|
| A | {{version_a}} | {{source_a}} | {{priority_a}} |
| B | {{version_b}} | {{source_b}} | {{priority_b}} |

→ 优先级判定：{{judgment}}
→ 处理方式：{{resolution}}
{{/each}}
{{/if}}
