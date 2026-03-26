import React from 'react';

interface TreeNode {
    event: string;
    children: TreeNode[];
}

interface ScenarioTreeProps {
    data: TreeNode[];
}

const TreeNodeComponent: React.FC<{ node: TreeNode; depth: number }> = ({ node, depth }) => {
    const colors = ['text-danger', 'text-warning', 'text-primary-light', 'text-success', 'text-text-muted'];
    const bgColors = ['bg-danger/10', 'bg-warning/10', 'bg-primary/10', 'bg-success/10', 'bg-panel'];
    const borderColors = ['border-danger/30', 'border-warning/30', 'border-primary/30', 'border-success/30', 'border-border'];
    const colorIdx = Math.min(depth, colors?.length - 1);

    return (
        <div className="relative">
            <div className={`${bgColors[colorIdx]} border ${borderColors[colorIdx]} rounded-lg px-3 py-2 text-xs font-bold ${colors[colorIdx]} inline-block max-w-xs`}>
                {node.event}
            </div>
            {node.children && node.children?.length > 0 && (
                <div className="ml-6 mt-2 pl-4 border-l-2 border-border/40 space-y-2">
                    {node.children?.map((child, i) => (
                        <TreeNodeComponent key={i} node={child} depth={depth + 1} />
                    ))}
                </div>
            )}
        </div>
    );
};

export const ScenarioTree: React.FC<ScenarioTreeProps> = ({ data }) => {
    if (!data || data?.length === 0) return null;

    return (
        <div className="space-y-3">
            {data?.map((root, i) => (
                <TreeNodeComponent key={i} node={root} depth={0} />
            ))}
        </div>
    );
};
