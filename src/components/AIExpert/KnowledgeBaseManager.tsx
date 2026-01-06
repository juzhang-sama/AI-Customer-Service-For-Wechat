
import React, { useState, useEffect, useRef } from 'react';

interface KnowledgeBaseManagerProps {
    boundPromptId?: number; // Optional: if provided, only show docs for this prompt
}

interface Document {
    id: number;
    file_name: string;
    file_type: string;
    file_size: number;
    bound_prompt_id: number;
    upload_time: string;
    description: string;
}

export const KnowledgeBaseManager: React.FC<KnowledgeBaseManagerProps> = ({ boundPromptId }) => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        loadDocuments();
    }, [boundPromptId]);

    const loadDocuments = async () => {
        setIsLoading(true);
        try {
            let url = 'http://localhost:5000/api/ai/documents';
            if (boundPromptId) {
                url += `?bound_prompt_id=${boundPromptId}`;
            }
            const response = await fetch(url);
            const data = await response.json();
            if (data.success) {
                setDocuments(data.documents);
            }
        } catch (error) {
            console.error('Failed to load documents:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Check size (e.g. 10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            alert('文件大小不能超过 10MB');
            return;
        }

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        if (boundPromptId) {
            formData.append('bound_prompt_id', boundPromptId.toString());
        } else {
            // Explicitly set to 0 for global if no boundPromptId
            formData.append('bound_prompt_id', '0');
        }
        formData.append('description', 'Uploaded via Web UI');

        try {
            const response = await fetch('http://localhost:5000/api/ai/documents', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (data.success) {
                alert('文件上传成功！');
                loadDocuments();
            } else {
                alert('上传失败: ' + data.error);
            }
        } catch (error) {
            console.error('Upload failed:', error);
            alert('上传出错');
        } finally {
            setIsUploading(false);
            // Reset input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleDelete = async (docId: number) => {
        if (!confirm('确定要删除这个文件吗？')) return;

        try {
            const response = await fetch(`http://localhost:5000/api/ai/documents/${docId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (data.success) {
                loadDocuments();
            } else {
                alert('删除失败: ' + data.error);
            }
        } catch (error) {
            console.error('Delete failed:', error);
            alert('删除出错');
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="space-y-4">
            {/* Header Actions */}
            <div className="flex justify-between items-center bg-gray-50 p-3 rounded-lg border border-gray-200">
                <div>
                    <h3 className="font-medium text-gray-700">
                        {boundPromptId ? '专家专属知识库' : '全局知识库'}
                    </h3>
                    <p className="text-xs text-gray-500">
                        {boundPromptId
                            ? '上传的文件仅当前专家可见'
                            : '上传的文件所有专家均可查阅 (如: 公司简介、通用话术)'}
                    </p>
                </div>
                <div>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        className="hidden"
                        accept=".pdf,.docx,.doc,.txt,.jpg,.png"
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors ${isUploading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-green-600 hover:bg-green-700 shadow-sm'
                            }`}
                    >
                        {isUploading ? '上传中...' : '+ 上传资料'}
                    </button>
                </div>
            </div>

            {/* Document List */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">文件名</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">大小</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">上传时间</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {isLoading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-8 text-center text-gray-500 text-sm">
                                    加载中...
                                </td>
                            </tr>
                        ) : documents.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-8 text-center text-gray-500 text-sm">
                                    暂无文件，请点击上方按钮上传
                                </td>
                            </tr>
                        ) : (
                            documents.map((doc) => (
                                <tr key={doc.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <span className="text-sm font-medium text-gray-900 truncate max-w-xs" title={doc.file_name}>
                                                {doc.file_name}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 uppercase">
                                            {doc.file_type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {formatFileSize(doc.file_size)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(doc.upload_time).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => handleDelete(doc.id)}
                                            className="text-red-600 hover:text-red-900"
                                        >
                                            删除
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
