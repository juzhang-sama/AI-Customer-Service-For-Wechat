import React, { useState, useEffect } from 'react';
import { Star, Trash2, Copy, Search, Tag } from 'lucide-react';

interface Favorite {
  id: number;
  question_type: string;
  customer_question: string;
  reply_text: string;
  tags: string[];
  usage_count: number;
  created_at: string;
}

export const FavoriteReplies: React.FC = () => {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/ai/favorites');
      const data = await response.json();
      
      if (data.success) {
        setFavorites(data.favorites.map((f: any) => ({
          ...f,
          tags: typeof f.tags === 'string' ? JSON.parse(f.tags) : f.tags
        })));
      }
    } catch (error) {
      console.error('Failed to load favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这条收藏吗？')) return;

    try {
      const response = await fetch(`http://localhost:5000/api/ai/favorites/${id}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        loadFavorites();
      }
    } catch (error) {
      console.error('Failed to delete favorite:', error);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  // 获取所有标签
  const allTags = Array.from(new Set(favorites.flatMap(f => f.tags)));

  // 过滤收藏
  const filteredFavorites = favorites.filter(f => {
    const matchesSearch = !searchQuery || 
      f.reply_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.customer_question.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTag = !selectedTag || f.tags.includes(selectedTag);
    
    return matchesSearch && matchesTag;
  });

  if (loading) {
    return <div className="p-6 text-center text-gray-500">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {/* 搜索和筛选 */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索收藏话术..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* 标签筛选 */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-2">
          <Tag className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <button
            onClick={() => setSelectedTag(null)}
            className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
              !selectedTag ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            全部
          </button>
          {allTags.map(tag => (
            <button
              key={tag}
              onClick={() => setSelectedTag(tag)}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
                selectedTag === tag ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* 收藏列表 */}
      {filteredFavorites.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <Star className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p>暂无收藏话术</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredFavorites.map(favorite => (
            <div
              key={favorite.id}
              className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
            >
              {/* 问题 */}
              {favorite.customer_question && (
                <div className="mb-2">
                  <span className="text-xs text-gray-500">客户问题：</span>
                  <p className="text-sm text-gray-600 mt-1">{favorite.customer_question}</p>
                </div>
              )}

              {/* 回复 */}
              <p className="text-sm text-gray-800 leading-relaxed mb-3 whitespace-pre-wrap">
                {favorite.reply_text}
              </p>

              {/* 标签和操作 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {favorite.tags.map((tag, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                  <span className="text-xs text-gray-400">使用 {favorite.usage_count} 次</span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleCopy(favorite.reply_text)}
                    className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                    title="复制"
                  >
                    <Copy className="w-4 h-4 text-gray-600" />
                  </button>
                  <button
                    onClick={() => handleDelete(favorite.id)}
                    className="p-1.5 hover:bg-red-50 rounded transition-colors"
                    title="删除"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

