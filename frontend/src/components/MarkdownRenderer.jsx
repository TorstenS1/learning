import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkGfm from 'remark-gfm';
import { ExternalLink } from 'lucide-react';
import 'katex/dist/katex.min.css'; // Import KaTeX CSS for math rendering

const MarkdownRenderer = ({ content, className = "" }) => {
    return (
        <div className={`prose prose-indigo max-w-none dark:prose-invert ${className}`}>
            <ReactMarkdown
                remarkPlugins={[remarkMath, remarkGfm]}
                rehypePlugins={[rehypeKatex]}
                components={{
                    // Custom link component - opens in new tab
                    a({ node, children, href, ...props }) {
                        return (
                            <a
                                href={href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 underline decoration-indigo-300 hover:decoration-indigo-500 transition-colors"
                                {...props}
                            >
                                {children}
                                <ExternalLink className="w-3 h-3 inline-block" />
                            </a>
                        );
                    },

                    // Custom heading component for Sources section
                    h3({ node, children, ...props }) {
                        const text = children?.toString() || '';
                        const isSourcesHeading = text.toLowerCase().includes('source') ||
                            text.toLowerCase().includes('quellen') ||
                            text.toLowerCase().includes('referenz');

                        if (isSourcesHeading) {
                            return (
                                <div className="mt-8 pt-6 border-t-2 border-indigo-200">
                                    <h3 className="text-xl font-bold text-indigo-700 mb-4 flex items-center gap-2" {...props}>
                                        <ExternalLink className="w-5 h-5" />
                                        {children}
                                    </h3>
                                </div>
                            );
                        }

                        return <h3 {...props}>{children}</h3>;
                    },

                    // Custom code block component
                    code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                            <pre className={`${className} bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto`} {...props}>
                                <code>{children}</code>
                            </pre>
                        ) : (
                            <code className={`${className} bg-indigo-50 text-indigo-900 px-1.5 py-0.5 rounded`} {...props}>
                                {children}
                            </code>
                        );
                    },

                    // Custom list component for sources
                    ul({ node, children, ...props }) {
                        // Check if this is likely a sources list (contains links)
                        const hasLinks = node?.children?.some(child =>
                            child.children?.some(c => c.tagName === 'a')
                        );

                        if (hasLinks) {
                            return (
                                <ul className="space-y-2 bg-indigo-50 p-4 rounded-lg border border-indigo-200" {...props}>
                                    {children}
                                </ul>
                            );
                        }

                        return <ul {...props}>{children}</ul>;
                    },

                    // Custom list item for sources
                    li({ node, children, ...props }) {
                        // Check if this list item contains a link
                        const hasLink = node?.children?.some(child => child.tagName === 'a');

                        if (hasLink) {
                            return (
                                <li className="flex items-start gap-2 text-sm" {...props}>
                                    <span className="text-indigo-500 mt-1">📚</span>
                                    <span className="flex-1">{children}</span>
                                </li>
                            );
                        }

                        return <li {...props}>{children}</li>;
                    }
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
};

export default MarkdownRenderer;
