import { useState, useEffect } from 'react';
import { disposalApi } from '../api/disposalApi';
import { Card } from '../components/common/Card';
import { CategoryBadge, StatusBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { History, Search, Filter } from 'lucide-react';

export const ScanHistory = () => {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  useEffect(() => {
    let isMounted = true;

    const fetchHistory = async () => {
      try {
        const data = await disposalApi.getHistory(50, 0);
        if (isMounted && Array.isArray(data)) {
          setHistory(data);
        }
      } catch (err) {
        console.warn('Scan history fetch error:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchHistory();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredHistory = history.filter((item) => {
    const matchesSearch =
      !searchQuery ||
      item.item_label?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.confirmed_category?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCat =
      selectedCategory === 'ALL' || item.confirmed_category === selectedCategory;

    return matchesSearch && matchesCat;
  });

  if (isLoading) {
    return <LoadingSpinner label="Loading scan history..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Scan History
        </h2>
        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Auditable chronological record of your verified waste disposals
        </p>
      </div>

      {/* Filter / Search Bar */}
      {history.length > 0 && (
        <Card padding="p-4" className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search history by item or category..."
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs md:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">All Categories</option>
              <option value="Wet">Wet Waste</option>
              <option value="Dry">Dry Waste</option>
              <option value="Sanitary">Sanitary Waste</option>
              <option value="Special Care">Special Care</option>
            </select>
          </div>
        </Card>
      )}

      {/* Table or Empty State */}
      {history.length === 0 ? (
        <EmptyState
          icon={History}
          title="No scans yet"
          description="Your verified waste scans will appear here."
          actionLabel="Scan your first item"
          actionPath="/scanner"
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs md:text-sm">
              <thead>
                <tr className="text-slate-400 uppercase text-[10px] font-bold tracking-wider border-b border-slate-100 dark:border-slate-800">
                  <th className="pb-3 px-3">Item Label</th>
                  <th className="pb-3 px-3">Category</th>
                  <th className="pb-3 px-3">Status</th>
                  <th className="pb-3 px-3">Credits Earned</th>
                  <th className="pb-3 px-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium text-slate-800 dark:text-slate-200">
                {filteredHistory.map((scan) => (
                  <tr key={scan.disposal_id || scan.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-3.5 px-3 font-semibold text-slate-900 dark:text-white">
                      {scan.item_label || 'Scanned Item'}
                    </td>
                    <td className="py-3.5 px-3">
                      <CategoryBadge category={scan.confirmed_category || scan.predicted_category} />
                    </td>
                    <td className="py-3.5 px-3">
                      <StatusBadge status={scan.verification_status} />
                    </td>
                    <td className="py-3.5 px-3 font-bold text-emerald-600 dark:text-emerald-400">
                      +{scan.credits_awarded || 10}
                    </td>
                    <td className="py-3.5 px-3 text-right text-xs text-slate-400">
                      {scan.timestamp ? new Date(scan.timestamp).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
