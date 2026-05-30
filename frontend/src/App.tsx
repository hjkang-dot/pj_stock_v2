import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

interface StockItem {
  stock_code: string;
  stock_name: string;
  market: string;
  security_group?: string;
  sector?: string;
  dart_corp_code?: string;
  listed_date?: string;
  listed_shares?: number;
  is_active: number;
}

interface FinancialReportItem {
  corp_code: string;
  stock_code?: string;
  bsns_year: number;
  fs_div?: string;
  fs_nm?: string;
  currency?: string;
  fiscal_period?: string;
  current_assets?: number;
  non_current_assets?: number;
  total_assets?: number;
  current_liabilities?: number;
  non_current_liabilities?: number;
  total_liabilities?: number;
  total_equity?: number;
  revenue?: number;
  operating_income?: number;
  net_income?: number;
  debt_ratio?: number;
  current_ratio?: number;
  equity_ratio?: number;
  operating_margin?: number;
  net_margin?: number;
  par_value?: number;
  eps?: number;
  cash_dividend_yield?: number;
  cash_dividend_per_share?: number;
  cash_dividend_total?: number;
  cash_dividend_payout_ratio?: number;
}

interface StockEvaluationItem {
  stock_code: string;
  business_year: number;
  base_date: string;
  close_price?: number;
  market_cap?: number;
  net_income?: number;
  total_equity?: number;
  debt_ratio?: number;
  roe?: number;
  per?: number;
  pbr?: number;
  dividend_yield?: number;
  cash_dividend_per_share?: number;
  payout_ratio?: number;
  dividend_years?: number;
  dividend_decrease_count?: number;
  financial_stability_score?: number;
  growth_score?: number;
  undervaluation_score?: number;
  shareholder_return_score?: number;
  market_governance_score?: number;
  total_score?: number;
  is_candidate?: number;
  current_ratio?: number;
  revenue_growth?: number;
  operating_income_growth?: number;
  eps_growth?: number;
}



interface DailyPriceItem {
  trade_date: string;
  stock_code: string;
  stock_name: string;
  market: string;
  section?: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  price_change: number;
  change_rate: number;
  volume: number;
  trading_value?: number;
  market_cap?: number;
  listed_shares?: number;
}



// Custom SVG Candlestick Chart Component
function CandlestickChart({ stockCode, stockName }: { stockCode: string; stockName: string }) {
  const [limit, setLimit] = useState(60); // Default to 3 Months (60 trading days)
  const [prices, setPrices] = useState<DailyPriceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const fetchPrices = async (code: string, daysLimit: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/stocks/${code}/prices?limit=${daysLimit}`);
      if (!response.ok) throw new Error("API Error");
      const data = await response.json();
      setPrices(data);
    } catch (err) {
      console.warn("Prices API failed. Error: ", err);
      setPrices([]);
      setError("주가 차트 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrices(stockCode, limit);
    setActiveIndex(null);
  }, [stockCode, limit]);

  if (loading && prices.length === 0) {
    return (
      <div className="chart-card loading-card">
        <div className="spinner"></div>
        <p>주가 차트 데이터를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-card error-card">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{error}</p>
        <button className="back-btn" style={{ padding: '0.4rem 1rem', marginTop: '0.5rem', fontSize: '0.85rem' }} onClick={() => fetchPrices(stockCode, limit)}>
          다시 시도
        </button>
      </div>
    );
  }

  if (prices.length === 0) {
    return (
      <div className="chart-card empty-card">
        <p>주가 데이터가 존재하지 않습니다.</p>
      </div>
    );
  }

  const svgWidth = 1000;
  const svgHeight = 360;
  const margin = { top: 25, right: 80, bottom: 40, left: 65 };
  
  const priceChartHeight = 180;
  const volumeChartHeight = 60;
  const priceChartTop = margin.top;
  const volumeChartTop = priceChartTop + priceChartHeight + 25;
  const chartWidth = svgWidth - margin.left - margin.right;

  const highPrices = prices.map(p => p.high_price);
  const lowPrices = prices.map(p => p.low_price);
  const maxPrice = Math.max(...highPrices);
  const minPrice = Math.min(...lowPrices);
  const priceRange = maxPrice - minPrice;
  const pad = priceRange * 0.08 || 100;
  
  const yMax = maxPrice + pad;
  const yMin = Math.max(0, minPrice - pad);
  const maxVolume = Math.max(...prices.map(p => p.volume));

  const getPriceY = (val: number) => priceChartTop + priceChartHeight - ((val - yMin) / (yMax - yMin || 1)) * priceChartHeight;
  const getVolumeHeight = (vol: number) => (vol / (maxVolume || 1)) * volumeChartHeight;
  const getVolumeY = (vol: number) => volumeChartTop + volumeChartHeight - getVolumeHeight(vol);
  const getX = (idx: number) => margin.left + (idx / (prices.length - 1 || 1)) * chartWidth;

  const activeItem = activeIndex !== null ? prices[activeIndex] : prices[prices.length - 1];

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xPos = e.clientX - rect.left;
    const logicalX = (xPos * svgWidth) / rect.width;
    const pct = (logicalX - margin.left) / chartWidth;
    const idx = Math.max(0, Math.min(prices.length - 1, Math.round(pct * (prices.length - 1))));
    setActiveIndex(idx);
  };

  const handleMouseLeave = () => {
    setActiveIndex(null);
  };

  const formatDate = (dateStr: string) => {
    if (dateStr.length !== 8) return dateStr;
    return `${dateStr.slice(4, 6)}/${dateStr.slice(6, 8)}`;
  };

  const candleWidth = Math.max(1, (chartWidth / prices.length) * 0.6);

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div className="chart-title-group">
          <h3>{stockName} 주가 흐름 (일봉)</h3>
          <div className="chart-legend-panel">
            <span className="legend-date">{activeItem.trade_date.slice(0,4)}-{activeItem.trade_date.slice(4,6)}-{activeItem.trade_date.slice(6,8)}</span>
            <span className="legend-item">시가: <span className="val">{activeItem.open_price.toLocaleString()}</span></span>
            <span className="legend-item">고가: <span className="val">{activeItem.high_price.toLocaleString()}</span></span>
            <span className="legend-item">저가: <span className="val">{activeItem.low_price.toLocaleString()}</span></span>
            <span className="legend-item">종가: <span className={`val ${activeItem.change_rate >= 0 ? 'color-up' : 'color-down'}`}>{activeItem.close_price.toLocaleString()}</span></span>
            <span className="legend-item">전일대비: <span className={`val ${activeItem.price_change >= 0 ? 'color-up' : 'color-down'}`}>{activeItem.price_change >= 0 ? `+${activeItem.price_change.toLocaleString()}` : activeItem.price_change.toLocaleString()}</span></span>
            <span className="legend-item">등락률: <span className={`val ${activeItem.change_rate >= 0 ? 'color-up' : 'color-down'}`}>{activeItem.change_rate >= 0 ? `+${activeItem.change_rate}%` : `${activeItem.change_rate}%`}</span></span>
            <span className="legend-item">거래량: <span className="val">{activeItem.volume.toLocaleString()}주</span></span>
          </div>
        </div>
        <div className="chart-period-tabs">
          <button className={`tab-btn ${limit === 20 ? 'active' : ''}`} onClick={() => setLimit(20)}>1개월</button>
          <button className={`tab-btn ${limit === 60 ? 'active' : ''}`} onClick={() => setLimit(60)}>3개월</button>
          <button className={`tab-btn ${limit === 120 ? 'active' : ''}`} onClick={() => setLimit(120)}>6개월</button>
          <button className={`tab-btn ${limit === 240 ? 'active' : ''}`} onClick={() => setLimit(240)}>1년</button>
        </div>
      </div>

      <div className="chart-svg-container">
        <svg 
          viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
          className="chart-svg"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Grid lines */}
          <line x1={margin.left} y1={priceChartTop} x2={svgWidth - margin.right} y2={priceChartTop} stroke="#e5e7eb" strokeWidth="0.8" />
          <line x1={margin.left} y1={priceChartTop + priceChartHeight / 2} x2={svgWidth - margin.right} y2={priceChartTop + priceChartHeight / 2} stroke="#f3f4f6" strokeWidth="0.8" />
          <line x1={margin.left} y1={priceChartTop + priceChartHeight} x2={svgWidth - margin.right} y2={priceChartTop + priceChartHeight} stroke="#e5e7eb" strokeWidth="0.8" />
          <line x1={margin.left} y1={volumeChartTop} x2={svgWidth - margin.right} y2={volumeChartTop} stroke="#e5e7eb" strokeWidth="0.8" />
          <line x1={margin.left} y1={volumeChartTop + volumeChartHeight} x2={svgWidth - margin.right} y2={volumeChartTop + volumeChartHeight} stroke="#e5e7eb" strokeWidth="0.8" />

          {/* Time scale */}
          {prices.map((item, idx) => {
            if (prices.length > 30 && idx % Math.floor(prices.length / 5) !== 0) return null;
            const x = getX(idx);
            return (
              <g key={`x-tick-${idx}`}>
                <line x1={x} y1={volumeChartTop + volumeChartHeight} x2={x} y2={volumeChartTop + volumeChartHeight + 5} stroke="#cbd5e1" strokeWidth="1" />
                <text x={x} y={volumeChartTop + volumeChartHeight + 20} textAnchor="middle" fontSize="11" fill="#64748b" fontWeight="500">
                  {formatDate(item.trade_date)}
                </text>
              </g>
            );
          })}

          {/* Price scale */}
          {[yMin, yMin + (yMax - yMin) / 2, yMax].map((val, idx) => (
            <text key={`y-tick-${idx}`} x={margin.left - 10} y={getPriceY(val) + 4} textAnchor="end" fontSize="11" fill="#64748b" fontWeight="500">
              {Math.round(val).toLocaleString()}원
            </text>
          ))}

          {/* Volume scale */}
          <text x={margin.left - 10} y={volumeChartTop + 4} textAnchor="end" fontSize="11" fill="#64748b" fontWeight="500">
            {Math.round(maxVolume).toLocaleString()}주
          </text>

          {/* Draw Candles */}
          {prices.map((item, idx) => {
            const x = getX(idx);
            const isUp = item.close_price >= item.open_price;
            const color = isUp ? "#e11d48" : "#2563eb";
            const topY = getPriceY(Math.max(item.open_price, item.close_price));
            const bottomY = getPriceY(Math.min(item.open_price, item.close_price));
            const bodyHeight = Math.max(1, bottomY - topY);

            return (
              <g key={`c-${idx}`}>
                <line 
                  x1={x} 
                  y1={getPriceY(item.high_price)} 
                  x2={x} 
                  y2={getPriceY(item.low_price)} 
                  stroke={color} 
                  strokeWidth="1.2" 
                />
                <rect 
                  x={x - candleWidth / 2} 
                  y={topY} 
                  width={candleWidth} 
                  height={bodyHeight} 
                  fill={color} 
                />
              </g>
            );
          })}

          {/* Draw Volume Bars */}
          {prices.map((item, idx) => {
            const x = getX(idx);
            const isUp = item.close_price >= item.open_price;
            const barFill = isUp ? "rgba(225, 29, 72, 0.2)" : "rgba(37, 99, 235, 0.2)";
            const barStroke = isUp ? "rgba(225, 29, 72, 0.5)" : "rgba(37, 99, 235, 0.5)";
            const volHeight = getVolumeHeight(item.volume);
            const volY = getVolumeY(item.volume);

            return (
              <rect 
                key={`v-${idx}`}
                x={x - candleWidth / 2}
                y={volY}
                width={candleWidth}
                height={volHeight}
                fill={barFill}
                stroke={barStroke}
                strokeWidth="0.7"
              />
            );
          })}

          {/* Hover crosshair tooltip */}
          {activeIndex !== null && (
            <g>
              <line 
                x1={getX(activeIndex)} 
                y1={priceChartTop - 10} 
                x2={getX(activeIndex)} 
                y2={volumeChartTop + volumeChartHeight + 10} 
                stroke="#6b7280" 
                strokeWidth="1.2" 
                strokeDasharray="4,4" 
              />
              <line 
                x1={margin.left - 10} 
                y1={getPriceY(activeItem.close_price)} 
                x2={svgWidth - margin.right + 10} 
                y2={getPriceY(activeItem.close_price)} 
                stroke="#6b7280" 
                strokeWidth="1.2" 
                strokeDasharray="4,4" 
              />

              <rect 
                x={svgWidth - margin.right} 
                y={getPriceY(activeItem.close_price) - 10} 
                width={72} 
                height={20} 
                fill="#1f2937" 
                rx="3" 
              />
              <text 
                x={svgWidth - margin.right + 36} 
                y={getPriceY(activeItem.close_price) + 4} 
                fill="#ffffff" 
                fontSize="10" 
                fontWeight="bold" 
                textAnchor="middle"
              >
                {activeItem.close_price.toLocaleString()}
              </text>

              <rect 
                x={getX(activeIndex) - 35} 
                y={volumeChartTop + volumeChartHeight + 25} 
                width={70} 
                height={18} 
                fill="#1f2937" 
                rx="3" 
              />
              <text 
                x={getX(activeIndex)} 
                y={volumeChartTop + volumeChartHeight + 37} 
                fill="#ffffff" 
                fontSize="10" 
                fontWeight="bold" 
                textAnchor="middle"
              >
                {formatDate(activeItem.trade_date)}
              </text>
            </g>
          )}
        </svg>
      </div>
    </div>
  );
}

interface EvaluatedStockItem {
  stock_code: string;
  stock_name: string;
  market: string;
  sector: string | null;
  business_year: number;
  base_date: string;
  close_price: number | null;
  market_cap: number | null;
  roe: number | null;
  per: number | null;
  pbr: number | null;
  dividend_yield: number | null;
  dividend_years: number | null;
  financial_stability_score: number | null;
  growth_score: number | null;
  undervaluation_score: number | null;
  shareholder_return_score: number | null;
  market_governance_score: number | null;
  total_score: number | null;
  is_candidate: number | null;
  current_ratio: number | null;
  revenue_growth: number | null;
  operating_income_growth: number | null;
  eps_growth: number | null;
}



// Fallback generator for 3-year mock financial reports if backend details API is offline


const formatWon = (value?: number): string => {
  if (value === undefined || value === null) return '-';
  const isNegative = value < 0;
  const absVal = Math.abs(value);
  let formatted = '';
  
  if (absVal >= 1_000_000_000_000) {
    formatted = `${(absVal / 1_000_000_000_000).toFixed(2)}조 원`;
  } else if (absVal >= 100_000_000) {
    formatted = `${(absVal / 100_000_000).toFixed(0)}억 원`;
  } else {
    formatted = `${absVal.toLocaleString()}원`;
  }
  
  return isNegative ? `-${formatted}` : formatted;
};

function App() {
  const [stocks, setStocks] = useState<StockItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState('');
  const [market, setMarket] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorStocks, setErrorStocks] = useState<string | null>(null);
  const [errorRanked, setErrorRanked] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);
  const [syncingPrices, setSyncingPrices] = useState(false);
  const [syncingFinancials, setSyncingFinancials] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [resettingDb, setResettingDb] = useState(false);

  // 검색 자동완성 상태
  const [suggestions, setSuggestions] = useState<StockItem[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const searchWrapperRef = useRef<HTMLDivElement>(null);
  const suggestDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Detail View State
  const [selectedStock, setSelectedStock] = useState<StockItem | null>(null);
  const [financials, setFinancials] = useState<FinancialReportItem[]>([]);
  const [loadingFinancials, setLoadingFinancials] = useState(false);
  const [evaluation, setEvaluation] = useState<StockEvaluationItem | null>(null);
  const [loadingEvaluation, setLoadingEvaluation] = useState(false);
  const [errorFinancials, setErrorFinancials] = useState<string | null>(null);
  const [errorEvaluation, setErrorEvaluation] = useState<string | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Tab State
  const [activeTab, setActiveTab] = useState<'list' | 'dividend'>('list');

  // Dividend rankings state
  const [rankedStocks, setRankedStocks] = useState<EvaluatedStockItem[]>([]);
  const [rankedTotal, setRankedTotal] = useState(0);
  const [rankedPage, setRankedPage] = useState(1);
  const [rankedPages, setRankedPages] = useState(1);
  const [rankedSearch, setRankedSearch] = useState('');
  const [rankedMarket, setRankedMarket] = useState('');
  const [onlyCandidates, setOnlyCandidates] = useState(false);
  const [loadingRanked, setLoadingRanked] = useState(false);
  
  // Summary KPIs for rankings
  const [candidateCount, setCandidateCount] = useState(0);
  const [avgScore, setAvgScore] = useState(0);

  const handleSyncPrices = async () => {
    setSyncingPrices(true);
    try {
      const response = await fetch("/api/stocks/sync-prices", {
        method: "POST",
      });
      if (!response.ok) throw new Error("Sync failed");
      const data = await response.json();
      if (data.status === "success") {
        if (data.processed_dates.length > 0) {
          alert(`주가 업데이트가 완료되었습니다!\n\n` +
                `• 동기화된 날짜: ${data.processed_dates.join(", ")}\n` +
                `• 적재된 데이터: ${data.upserted_rows.toLocaleString()}건\n` +
                `• 남은 누락 영업일: ${data.remaining_missing_count}일 ${data.remaining_missing_count > 0 ? '(더 채우려면 버튼을 다시 클릭해 주세요)' : ''}`);
        } else {
          alert(`이미 모든 평일의 주가 데이터가 최신 상태입니다.`);
        }
        fetchStocks();
        if (selectedStock) {
          fetchFinancials(selectedStock.stock_code);
        }
      } else {
        alert(`업데이트 중 오류 발생: ${data.message}`);
      }
    } catch (err) {
      console.error(err);
      alert("주가 업데이트 요청에 실패했습니다.");
    } finally {
      setSyncingPrices(false);
    }
  };

  const handleEvaluate = async () => {
    const confirmed = window.confirm(
      "최신 주가 기준으로 전체 종목의 투자 점수를 다시 계산합니다.\n(재무 데이터가 없는 종목은 제외됩니다.)\n\n계속할까요?"
    );
    if (!confirmed) return;

    setEvaluating(true);
    try {
      const response = await fetch("/api/stocks/evaluate", {
        method: "POST",
      });
      if (!response.ok) throw new Error("Evaluate failed");
      const data = await response.json();
      if (data.status === "success") {
        alert(`점수 계산이 완료되었습니다!\n\n` +
              `• 평가 기준일: ${data.base_date ? `${data.base_date.slice(0,4)}-${data.base_date.slice(4,6)}-${data.base_date.slice(6,8)}` : '-'}\n` +
              `• 재무 데이터 연도: ${data.business_year}년\n` +
              `• 점수 계산 완료: ${data.evaluation_rows.toLocaleString()}개 종목`);
        fetchRankedStocks();
        fetchRankingsSummary();
        if (selectedStock) fetchEvaluation(selectedStock.stock_code);
      } else {
        alert(`점수 계산 중 오류 발생:\n${data.message}`);
      }
    } catch (err) {
      console.error(err);
      alert("점수 계산 요청에 실패했습니다.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleResetDatabase = async () => {
    const confirmed = window.confirm(
      "재무/배당 테이블(company_financials)만 초기화합니다.\n종목 목록과 주가 데이터는 유지됩니다.\n\n계속할까요?"
    );
    if (!confirmed) return;

    setResettingDb(true);
    try {
      const response = await fetch("/api/stocks/reset-db", {
        method: "POST",
      });
      if (!response.ok) throw new Error("Database reset failed");

      setSelectedStock(null);
      setFinancials([]);
      setEvaluation(null);
      setRankedStocks([]);
      setRankedTotal(0);
      setRankedPage(1);
      setRankedPages(1);
      setCandidateCount(0);
      setAvgScore(0);

      alert("재무/배당 테이블 초기화가 완료되었습니다. DART 재무/배당 데이터를 다시 적재해 주세요.");
    } catch (err) {
      console.error(err);
      alert("재무/배당 테이블 초기화 요청에 실패했습니다. 백엔드 서버 상태를 확인해 주세요.");
    } finally {
      setResettingDb(false);
    }
  };

  const handleSyncFinancials = async () => {
    const limitInput = window.prompt(
      "DART 재무/배당 데이터를 수집할 기업 수를 입력하세요.\n처음에는 10 정도로 테스트하는 것을 권장합니다. 전체 수집은 0을 입력하세요.",
      "10"
    );
    if (limitInput === null) return;

    const limit = Number(limitInput.trim());
    if (!Number.isInteger(limit) || limit < 0) {
      alert("기업 수는 0 이상의 정수로 입력해 주세요.");
      return;
    }

    const confirmed = window.confirm(
      `2025년 사업보고서 기준으로 ${limit === 0 ? "전체 기업" : `${limit}개 기업`}의 재무/배당 데이터를 수집하고 company_financials에 저장합니다.\n\n계속할까요?`
    );
    if (!confirmed) return;

    setSyncingFinancials(true);
    try {
      const params = new URLSearchParams({
        business_year: "2025",
        report_code: "11011",
        limit: limit.toString(),
        sleep_seconds: limit === 0 ? "1" : "0.5",
      });
      const response = await fetch(`/api/stocks/sync-financials?${params.toString()}`, {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = data.detail || {};
        const output = detail.output || data.output || "";
        const message = detail.message || data.message || "Financial sync failed";
        throw new Error(output ? `${message}\n\n${output}` : message);
      }
      if (data.status !== "success") {
        throw new Error(data.output || data.message || "Financial sync failed");
      }

      alert("DART 재무/배당 데이터 수집 및 DB 저장이 완료되었습니다.");
      if (selectedStock) {
        fetchFinancials(selectedStock.stock_code);
        fetchEvaluation(selectedStock.stock_code);
      }
      if (activeTab === 'dividend') {
        fetchRankedStocks();
        fetchRankingsSummary();
      }
    } catch (err) {
      console.error(err);
      const message = err instanceof Error ? err.message : String(err);
      alert(`DART 재무/배당 데이터 수집 또는 DB 저장에 실패했습니다.\n\n${message.slice(-3000)}`);
    } finally {
      setSyncingFinancials(false);
    }
  };

  const fetchStocks = async () => {
    setLoading(true);
    setErrorStocks(null);
    setUsingFallback(false);

    const pageSize = 15;
    const params = new URLSearchParams({
      page: page.toString(),
      size: pageSize.toString(),
    });
    if (search.trim()) params.append('search', search);
    if (market) params.append('market', market);

    try {
      const response = await fetch(`/api/stocks?${params.toString()}`);
      if (!response.ok) {
        throw new Error('API server returned error');
      }
      const data = await response.json();
      setStocks(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      console.warn("Backend API is offline or failed. Error: ", err);
      setUsingFallback(true);
      setErrorStocks("종목 데이터를 불러오지 못했습니다. 서버 상태를 확인하거나 잠시 후 다시 시도해 주세요.");
      setStocks([]);
      setTotal(0);
      setPages(1);
    } finally {
      setLoading(false);
    }
  };

  const fetchFinancials = async (stockCode: string) => {
    setLoadingFinancials(true);
    setErrorFinancials(null);
    try {
      const response = await fetch(`/api/stocks/${stockCode}/financials`);
      if (!response.ok) {
        throw new Error('재무 데이터를 불러오는 데 실패했습니다.');
      }
      const data = await response.json();
      const sorted = data.sort((a: any, b: any) => (b.bsns_year || 0) - (a.bsns_year || 0));
      setFinancials(sorted);
    } catch (err) {
      console.warn("Backend Details API failed. Error: ", err);
      setFinancials([]);
      setErrorFinancials("재무 데이터를 로드할 수 없습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLoadingFinancials(false);
    }
  };

  const fetchEvaluation = async (stockCode: string) => {
    setLoadingEvaluation(true);
    setErrorEvaluation(null);
    try {
      const response = await fetch(`/api/stocks/${stockCode}/evaluation`);
      if (!response.ok) {
        throw new Error('평가 지표를 불러오는 데 실패했습니다.');
      }
      const data = await response.json();
      if (!data) {
        throw new Error('평가 데이터가 존재하지 않습니다.');
      }
      setEvaluation(data);
    } catch (err) {
      console.warn("Backend Evaluation API failed. Error: ", err);
      setEvaluation(null);
      setErrorEvaluation("투자 평가 데이터를 로드할 수 없습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLoadingEvaluation(false);
    }
  };

  const fetchRankedStocks = async () => {
    setLoadingRanked(true);
    setErrorRanked(null);
    const pageSize = 15;
    const params = new URLSearchParams({
      page: rankedPage.toString(),
      size: pageSize.toString(),
    });
    if (rankedSearch.trim()) params.append('search', rankedSearch);
    if (rankedMarket) params.append('market', rankedMarket);
    if (onlyCandidates) params.append('is_candidate', '1');

    try {
      const response = await fetch(`/api/stocks/rankings?${params.toString()}`);
      if (!response.ok) throw new Error("Rankings API Error");
      const data = await response.json();
      setRankedStocks(data.items);
      setRankedTotal(data.total);
      setRankedPages(data.pages);
    } catch (err) {
      console.warn("Rankings API failed. Error: ", err);
      setErrorRanked("평가 순위 데이터를 불러오지 못했습니다. 서버 상태를 확인하거나 잠시 후 다시 시도해 주세요.");
      setRankedStocks([]);
      setRankedTotal(0);
      setRankedPages(1);
    } finally {
      setLoadingRanked(false);
    }
  };

  const fetchRankingsSummary = async () => {
    try {
      const response = await fetch("/api/stocks/rankings?is_candidate=1&size=100");
      if (response.ok) {
        const data = await response.json();
        setCandidateCount(data.total);
        if (data.items.length > 0) {
          const sum = data.items.reduce((acc: number, item: any) => acc + (item.total_score || 0), 0);
          setAvgScore(Number((sum / data.items.length).toFixed(1)));
        }
      }
    } catch (e) {
      console.warn("Rankings summary fetch failed. Error: ", e);
      setCandidateCount(0);
      setAvgScore(0);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, [page, market]);

  useEffect(() => {
    if (activeTab === 'dividend') {
      fetchRankedStocks();
    }
  }, [rankedPage, rankedMarket, onlyCandidates, activeTab]);

  useEffect(() => {
    if (activeTab === 'dividend') {
      fetchRankingsSummary();
    }
  }, [activeTab]);

  // 자동완성: 검색어 입력 시 API 호출 (300ms debounce)
  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query.trim() || query.trim().length < 1) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }
    try {
      const params = new URLSearchParams({ search: query, size: '8', page: '1' });
      if (market) params.append('market', market);
      const res = await fetch(`/api/stocks?${params.toString()}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setSuggestions(data.items || []);
      setShowDropdown((data.items || []).length > 0);
      setHighlightedIndex(-1);
    } catch {
      setSuggestions([]);
      setShowDropdown(false);
      setHighlightedIndex(-1);
    }
  }, [market]);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearch(val);
    if (suggestDebounceRef.current) clearTimeout(suggestDebounceRef.current);
    suggestDebounceRef.current = setTimeout(() => fetchSuggestions(val), 300);
  };

  const handleSuggestionSelect = (stock: StockItem) => {
    setSearch(stock.stock_name);
    setSuggestions([]);
    setShowDropdown(false);
    setHighlightedIndex(-1);
    handleStockClick(stock);
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showDropdown && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedIndex(i => Math.min(i + 1, suggestions.length - 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedIndex(i => Math.max(i - 1, -1));
        return;
      }
      if (e.key === 'Enter' && highlightedIndex >= 0) {
        e.preventDefault();
        handleSuggestionSelect(suggestions[highlightedIndex]);
        return;
      }
      if (e.key === 'Escape') {
        setShowDropdown(false);
        setHighlightedIndex(-1);
        return;
      }
    }
    if (e.key === 'Enter') {
      setShowDropdown(false);
      setPage(1);
      fetchStocks();
    }
  };

  const handleSearchSubmit = () => {
    setShowDropdown(false);
    setPage(1);
    fetchStocks();
  };

  // 검색창 바깥 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
        setHighlightedIndex(-1);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleRankedSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      setRankedPage(1);
      fetchRankedStocks();
    }
  };

  const handleRankedSearchSubmit = () => {
    setRankedPage(1);
    fetchRankedStocks();
  };

  const handleTabChange = (tab: 'list' | 'dividend') => {
    setSelectedStock(null);
    setActiveTab(tab);
  };

  const handleStockClick = (stock: StockItem) => {
    setSelectedStock(stock);
    fetchFinancials(stock.stock_code);
    fetchEvaluation(stock.stock_code);
  };

  // Render Detailed Financial Page
  if (selectedStock) {
    const isHigh = (evaluation?.total_score || 0) >= 70;
    const isMid = (evaluation?.total_score || 0) >= 60 && (evaluation?.total_score || 0) < 70;
    const scoreClass = isHigh ? 'score-high' : isMid ? 'score-mid' : 'score-low';
    
    return (
      <div className="app-container">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="logo-section">
            <div className="logo-icon">S</div>
            <span className="logo-text">Stock Finder V2</span>
          </div>
          <nav>
            <ul className="nav-menu">
              <li 
                className={`nav-item ${activeTab === 'list' ? 'active' : ''}`}
                onClick={() => handleTabChange('list')}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
                종목 조회
              </li>
              <li 
                className={`nav-item ${activeTab === 'dividend' ? 'active' : ''}`}
                onClick={() => handleTabChange('dividend')}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                배당주 분석
              </li>
              <li className="nav-item">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                가상 테스트 (준비중)
              </li>
              <li>
                <button
                  type="button"
                  className="reset-db-btn"
                  onClick={handleResetDatabase}
                  disabled={resettingDb}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14H6L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path><path d="M9 6V4h6v2"></path></svg>
                  {resettingDb ? "재무 초기화 중..." : "재무 DB 초기화"}
                </button>
              </li>
            </ul>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          <div>
            <button className="back-btn" onClick={() => setSelectedStock(null)}>
              ← 목록으로 돌아가기
            </button>
          </div>

          <header className="stock-detail-header">
            <div className="stock-meta-badges">
              <span className={`market-badge ${selectedStock.market.toLowerCase()}`}>{selectedStock.market}</span>
              {selectedStock.sector && <span className="badge">{selectedStock.sector}</span>}
              <span className="badge">종목코드: {selectedStock.stock_code}</span>
              {selectedStock.dart_corp_code && <span className="badge">DART 기업코드: {selectedStock.dart_corp_code}</span>}
              {evaluation?.is_candidate === 1 && <span className="badge primary">🌟 배당 우수 추천 종목</span>}
            </div>
            <h1>{selectedStock.stock_name} 상세 재무 분석</h1>
            <p>선택된 상장 기업의 연도별 연결 재무실적 및 주당 배당금 추이 현황을 조회합니다.</p>
          </header>

          {/* Evaluation Section */}
          {loadingEvaluation ? (
            <div className="chart-card loading-card" style={{ height: '180px' }}>
              <div className="spinner"></div>
              <p>투자 평가 지표를 분석하는 중...</p>
            </div>
          ) : errorEvaluation ? (
            <div className="chart-card error-card" style={{ height: '180px' }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <p style={{ fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{errorEvaluation}</p>
              <button className="back-btn" style={{ padding: '0.4rem 1rem', marginTop: '0.5rem', fontSize: '0.85rem' }} onClick={() => fetchEvaluation(selectedStock.stock_code)}>
                다시 시도
              </button>
            </div>
          ) : evaluation ? (
            <div className="evaluation-card">
              <div className="evaluation-header">
                <div className="eval-title-group">
                  <h3>투자 가치 및 배당주 매력도 분석</h3>
                  <span className="eval-as-of">평가 기준일: {evaluation.base_date ? `${evaluation.base_date.slice(0,4)}-${evaluation.base_date.slice(4,6)}-${evaluation.base_date.slice(6,8)}` : '-'} ({evaluation.business_year}년 결산 기준)</span>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button className="sync-btn" style={{ padding: '0.45rem 1rem', fontSize: '0.85rem', background: 'linear-gradient(135deg, #4f46e5, #3b82f6)', boxShadow: '0 2px 6px rgba(59, 130, 246, 0.2)' }} onClick={() => setShowDetailsModal(true)}>
                    🔍 점수 산출 내역 보기
                  </button>
                  {evaluation.is_candidate === 1 && (
                    <span className="candidate-badge-large">🌟 추천 배당주 후보군 지정</span>
                  )}
                </div>
              </div>
              
              <div className="evaluation-body">
                {/* 1. Total Score Panel */}
                <div className="eval-score-panel">
                  <span className="panel-subtitle">종합 투자 점수</span>
                  <div className={`score-circle ${scoreClass}`}>
                    <span className="score-num">{evaluation.total_score !== undefined && evaluation.total_score !== null ? Math.round(evaluation.total_score) : '-'}</span>
                    <span className="score-max">/ 100점</span>
                  </div>
                  <span className="score-desc">
                    {evaluation.total_score !== undefined && evaluation.total_score !== null && evaluation.total_score >= 70
                      ? '재무 건전성과 배당 매력도가 최고 수준인 종목입니다.'
                      : evaluation.total_score !== undefined && evaluation.total_score !== null && evaluation.total_score >= 60
                      ? '안정적이지만 밸류에이션 조정이 필요할 수 있습니다.'
                      : '투자 가치 기준점보다 하위에 위치한 종목입니다.'}
                  </span>
                </div>

                {/* 2. Subscores Panel */}
                <div className="eval-subscores-panel">
                  <span className="panel-subtitle">평가 부문별 상세 점수</span>
                  
                  <div className="subscore-item">
                    <div className="subscore-header">
                      <span>금융 재무 안정성 (안정성)</span>
                      <span className="subscore-val">{evaluation.financial_stability_score || 0} / 15점</span>
                    </div>
                    <div className="progress-bg">
                      <div className="progress-bar color-stability" style={{ width: `${((evaluation.financial_stability_score || 0) / 15) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="subscore-item">
                    <div className="subscore-header">
                      <span>본업 지속 성장성 (성장성)</span>
                      <span className="subscore-val">{evaluation.growth_score || 0} / 15점</span>
                    </div>
                    <div className="progress-bg">
                      <div className="progress-bar color-growth" style={{ width: `${((evaluation.growth_score || 0) / 15) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="subscore-item">
                    <div className="subscore-header">
                      <span>가격 매력도 및 저평가 (밸류에이션)</span>
                      <span className="subscore-val">{evaluation.undervaluation_score || 0} / 25점</span>
                    </div>
                    <div className="progress-bg">
                      <div className="progress-bar color-undervaluation" style={{ width: `${((evaluation.undervaluation_score || 0) / 25) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="subscore-item">
                    <div className="subscore-header">
                      <span>주주 환원 및 배당 매력 (수익성)</span>
                      <span className="subscore-val">{evaluation.shareholder_return_score || 0} / 25점</span>
                    </div>
                    <div className="progress-bg">
                      <div className="progress-bar color-return" style={{ width: `${((evaluation.shareholder_return_score || 0) / 25) * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="subscore-item">
                    <div className="subscore-header">
                      <span>시장 및 지배구조 리스크 (신뢰성)</span>
                      <span className="subscore-val">{evaluation.market_governance_score || 0} / 20점</span>
                    </div>
                    <div className="progress-bg">
                      <div className="progress-bar color-governance" style={{ width: `${((evaluation.market_governance_score || 0) / 20) * 100}%` }}></div>
                    </div>
                  </div>
                </div>

                {/* 3. Valuation metrics Grid */}
                <div className="eval-metrics-panel">
                  <span className="panel-subtitle">핵심 투자비율 (Valuation)</span>
                  <div className="metrics-grid">
                    <div className="metric-box">
                      <span className="label">ROE (자기자본이익률)</span>
                      <span className="val">{evaluation.roe !== undefined && evaluation.roe !== null ? `${evaluation.roe.toFixed(2)}%` : '-'}</span>
                    </div>
                    <div className="metric-box">
                      <span className="label">PER (주가수익비율)</span>
                      <span className="val">{evaluation.per !== undefined && evaluation.per !== null ? `${evaluation.per.toFixed(2)}배` : '-'}</span>
                    </div>
                    <div className="metric-box">
                      <span className="label">PBR (주가순자산비율)</span>
                      <span className="val">{evaluation.pbr !== undefined && evaluation.pbr !== null ? `${evaluation.pbr.toFixed(2)}배` : '-'}</span>
                    </div>
                    <div className="metric-box">
                      <span className="label">배당 수익률 (Yield)</span>
                      <span className="val" style={{ color: '#047857' }}>{evaluation.dividend_yield !== undefined && evaluation.dividend_yield !== null ? `${evaluation.dividend_yield.toFixed(2)}%` : '-'}</span>
                    </div>
                    <div className="metric-box" style={{ gridColumn: 'span 2' }}>
                      <span className="label">배당 지급 연수 및 삭감 횟수</span>
                      <span className="val" style={{ fontSize: '0.9rem' }}>
                        {evaluation.dividend_years || 0}년 연속 / 삭감 {evaluation.dividend_decrease_count || 0}회
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {/* SVG Candlestick Chart Component */}
          <CandlestickChart 
            stockCode={selectedStock.stock_code}
            stockName={selectedStock.stock_name}
          />

          <div className="detail-section">
            {/* Section 1: Financials Sheet */}
            <div>
              <h3 className="section-title">연도별 재무 경영 실적 (손익/상태표)</h3>
              <div className="financials-table-wrapper">
                <table className="stock-table">
                  <thead>
                    <tr>
                      <th>조회 연도</th>
                      <th className="hide-on-mobile">제표 종류</th>
                      <th className="number-align">연간 매출액</th>
                      <th className="number-align">영업 이익</th>
                      <th className="number-align hide-on-mobile">영업 이익률</th>
                      <th className="number-align">당기 순이익</th>
                      <th className="number-align hide-on-mobile">순이익률</th>
                      <th className="number-align hide-on-tablet">자산 총계</th>
                      <th className="number-align hide-on-tablet">부채 총계</th>
                      <th className="number-align">자본 총계</th>
                      <th className="number-align">부채 비율</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loadingFinancials ? (
                      <tr>
                        <td colSpan={11} style={{ textAlign: 'center', padding: '3rem' }}>
                          <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
                          데이터를 조회하고 있습니다...
                        </td>
                      </tr>
                    ) : errorFinancials ? (
                      <tr>
                        <td colSpan={11} style={{ textAlign: 'center', padding: '3rem' }}>
                          <svg style={{ margin: '0 auto 1rem' }} width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                          <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{errorFinancials}</p>
                          <button className="back-btn" style={{ padding: '0.4rem 1rem', marginTop: '0.75rem', fontSize: '0.85rem', display: 'inline-flex' }} onClick={() => fetchFinancials(selectedStock.stock_code)}>
                            다시 시도
                          </button>
                        </td>
                      </tr>
                    ) : financials.length === 0 ? (
                      <tr>
                        <td colSpan={11} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                          공시된 재무제표 실적이 존재하지 않습니다.
                        </td>
                      </tr>
                    ) : (
                      financials.map((fin) => (
                        <tr key={fin.bsns_year}>
                          <td style={{ fontWeight: 600 }}>{fin.bsns_year}년</td>
                          <td className="hide-on-mobile" style={{ color: 'var(--text-secondary)' }}>{fin.fs_nm || '연결재무제표'}</td>
                          <td className="number-align" style={{ fontWeight: 500 }}>{formatWon(fin.revenue)}</td>
                          <td className="number-align" style={{ fontWeight: 500 }}>{formatWon(fin.operating_income)}</td>
                          <td className="number-align hide-on-mobile" style={{ color: 'var(--text-secondary)' }}>
                            {fin.operating_margin !== undefined && fin.operating_margin !== null ? `${fin.operating_margin.toFixed(2)}%` : '-'}
                          </td>
                          <td className="number-align" style={{ fontWeight: 500 }}>{formatWon(fin.net_income)}</td>
                          <td className="number-align hide-on-mobile" style={{ color: 'var(--text-secondary)' }}>
                            {fin.net_margin !== undefined && fin.net_margin !== null ? `${fin.net_margin.toFixed(2)}%` : '-'}
                          </td>
                          <td className="number-align hide-on-tablet">{formatWon(fin.total_assets)}</td>
                          <td className="number-align hide-on-tablet">{formatWon(fin.total_liabilities)}</td>
                          <td className="number-align" style={{ fontWeight: 500 }}>{formatWon(fin.total_equity)}</td>
                          <td className="number-align">
                            {fin.debt_ratio !== undefined && fin.debt_ratio !== null ? `${fin.debt_ratio.toFixed(2)}%` : '-'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section 2: Dividends Sheet */}
            <div>
              <h3 className="section-title">연도별 주주 환원 및 배당 추이</h3>
              <div className="financials-table-wrapper">
                <table className="stock-table">
                  <thead>
                    <tr>
                      <th>조회 연도</th>
                      <th className="number-align hide-on-mobile">주당 액면가</th>
                      <th className="number-align">주당 순이익(EPS)</th>
                      <th className="number-align">주당 배당금(DPS)</th>
                      <th className="number-align hide-on-tablet">총 배당 지급액</th>
                      <th className="number-align">배당 수익률</th>
                      <th className="number-align hide-on-mobile">배당 성향</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loadingFinancials ? (
                      <tr>
                        <td colSpan={7} style={{ textAlign: 'center', padding: '3rem' }}>
                          <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
                          배당 데이터를 조회하고 있습니다...
                        </td>
                      </tr>
                    ) : errorFinancials ? (
                      <tr>
                        <td colSpan={7} style={{ textAlign: 'center', padding: '3rem' }}>
                          <svg style={{ margin: '0 auto 1rem' }} width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                          <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{errorFinancials}</p>
                          <button className="back-btn" style={{ padding: '0.4rem 1rem', marginTop: '0.75rem', fontSize: '0.85rem', display: 'inline-flex' }} onClick={() => fetchFinancials(selectedStock.stock_code)}>
                            다시 시도
                          </button>
                        </td>
                      </tr>
                    ) : financials.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                          공시된 배당 내역이 존재하지 않습니다.
                        </td>
                      </tr>
                    ) : (
                      financials.map((fin) => (
                        <tr key={fin.bsns_year}>
                          <td style={{ fontWeight: 600 }}>{fin.bsns_year}년</td>
                          <td className="number-align hide-on-mobile" style={{ color: 'var(--text-secondary)' }}>
                            {fin.par_value ? `${fin.par_value.toLocaleString()}원` : '-'}
                          </td>
                          <td className="number-align" style={{ fontWeight: 500 }}>
                            {fin.eps ? `${fin.eps.toLocaleString()}원` : '-'}
                          </td>
                          <td className="number-align" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                            {fin.cash_dividend_per_share ? `${fin.cash_dividend_per_share.toLocaleString()}원` : '-'}
                          </td>
                          <td className="number-align hide-on-tablet">
                            {fin.cash_dividend_total ? formatWon(fin.cash_dividend_total) : '-'}
                          </td>
                          <td className="number-align text-success" style={{ fontWeight: 600 }}>
                            {fin.cash_dividend_yield !== undefined && fin.cash_dividend_yield !== null ? `${fin.cash_dividend_yield.toFixed(2)}%` : '-'}
                          </td>
                          <td className="number-align hide-on-mobile">
                            {fin.cash_dividend_payout_ratio !== undefined && fin.cash_dividend_payout_ratio !== null ? `${fin.cash_dividend_payout_ratio.toFixed(2)}%` : '-'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>

        {showDetailsModal && evaluation && (
          <ScoreDetailsOverlay 
            evaluation={evaluation} 
            onClose={() => setShowDetailsModal(false)} 
          />
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">S</div>
          <span className="logo-text">Stock Finder V2</span>
        </div>
        <nav>
          <ul className="nav-menu">
            <li 
              className={`nav-item ${activeTab === 'list' ? 'active' : ''}`}
              onClick={() => handleTabChange('list')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
              종목 조회
            </li>
            <li 
              className={`nav-item ${activeTab === 'dividend' ? 'active' : ''}`}
              onClick={() => handleTabChange('dividend')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
              배당주 분석
            </li>
            <li className="nav-item">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              가상 테스트 (준비중)
            </li>
            <li>
              <button
                type="button"
                className="reset-db-btn"
                onClick={handleResetDatabase}
                disabled={resettingDb}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14H6L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path><path d="M9 6V4h6v2"></path></svg>
                {resettingDb ? "재무 초기화 중..." : "재무 DB 초기화"}
              </button>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'list' ? (
          <>
            <header className="header-section">
              <div className="header-title">
                <h1>전체 상장 종목 조회</h1>
                <p>한국거래소(KRX)에 등록된 전체 활성 종목들의 실시간 목록을 조회합니다. 종목을 클릭하여 상세 재무 정보를 볼 수 있습니다.</p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {usingFallback && (
                  <span style={{ fontSize: '0.8rem', backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.35rem 0.75rem', borderRadius: '20px', fontWeight: 600 }}>
                    ⚠️ 데모용 오프라인 모드
                  </span>
                )}
                {!usingFallback && (
                  <>
                    <button
                      className={`sync-btn financial-sync-btn ${syncingFinancials ? 'loading' : ''}`}
                      onClick={handleSyncFinancials}
                      disabled={syncingFinancials || syncingPrices}
                    >
                      <svg className="sync-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M4 19h16"></path><path d="M4 15h16"></path><path d="M8 11V5h8v6"></path><path d="M12 5v6"></path>
                      </svg>
                      {syncingFinancials ? "재무 수집 중..." : "재무 수집/저장"}
                    </button>
                    <button
                      className={`sync-btn ${syncingPrices ? 'loading' : ''}`}
                      onClick={handleSyncPrices}
                      disabled={syncingPrices || syncingFinancials}
                    >
                      <svg className="sync-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
                      </svg>
                      {syncingPrices ? "주가 업데이트 중..." : "주가 업데이트"}
                    </button>
                  </>
                )}
              </div>
            </header>

            {/* Summary grid */}
            <section className="summary-grid">
              <div className="summary-card">
                <span className="card-title">총 상장 종목 수</span>
                <span className="card-value">{total.toLocaleString()}개</span>
              </div>
              <div className="summary-card">
                <span className="card-title">선택된 시장 구분</span>
                <span className="card-value">{market || '전체 시장'}</span>
              </div>
              <div className="summary-card">
                <span className="card-title">현재 페이지</span>
                <span className="card-value">{page} / {pages}</span>
              </div>
            </section>

            {/* Filters and Searches */}
            <section className="controls-card">
              <div className="search-filter-row">
                <div className="search-input-wrapper autocomplete-wrapper" ref={searchWrapperRef}>
                  <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  <input
                    type="text"
                    placeholder="종목명, 종목코드, 업종 입력 시 자동완성..."
                    className="search-input"
                    value={search}
                    onChange={handleSearchInputChange}
                    onKeyDown={handleSearchKeyPress}
                    onFocus={() => { if (suggestions.length > 0) setShowDropdown(true); }}
                    autoComplete="off"
                  />
                  {/* 자동완성 드롭다운 */}
                  {showDropdown && suggestions.length > 0 && (
                    <ul className="autocomplete-dropdown">
                      {suggestions.map((stock, idx) => (
                        <li
                          key={stock.stock_code}
                          className={`autocomplete-item${highlightedIndex === idx ? ' highlighted' : ''}`}
                          onMouseDown={(e) => { e.preventDefault(); handleSuggestionSelect(stock); }}
                          onMouseEnter={() => setHighlightedIndex(idx)}
                        >
                          <span className="ac-code">{stock.stock_code}</span>
                          <span className="ac-name">{stock.stock_name}</span>
                          <span className={`ac-market market-badge ${stock.market.toLowerCase()}`}>{stock.market}</span>
                          {stock.sector && <span className="ac-sector">{stock.sector}</span>}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                
                <select 
                  className="market-select"
                  value={market}
                  onChange={(e) => { setMarket(e.target.value); setPage(1); }}
                >
                  <option value="">모든 시장</option>
                  <option value="KOSPI">KOSPI</option>
                  <option value="KOSDAQ">KOSDAQ</option>
                </select>

                <button 
                  className="page-btn active" 
                  style={{ padding: '0.5rem 1.5rem', borderRadius: '10px' }}
                  onClick={handleSearchSubmit}
                >
                  조회
                </button>
              </div>
            </section>

            {/* Table representation */}
            <section className="table-wrapper">
              {loading ? (
                <div className="loading-wrapper">
                  <div className="spinner"></div>
                  <p>종목 목록을 서버에서 불러오는 중입니다...</p>
                </div>
              ) : errorStocks ? (
                <div className="error-card" style={{ margin: '2rem auto', maxWidth: '400px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.75rem', marginBottom: '0.75rem' }}>{errorStocks}</p>
                  <button className="back-btn" style={{ padding: '0.4rem 1.2rem', fontSize: '0.85rem' }} onClick={fetchStocks}>
                    다시 시도
                  </button>
                </div>
              ) : stocks.length === 0 ? (
                <div className="empty-wrapper">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                  <p>조건을 만족하는 상장 종목이 존재하지 않습니다.</p>
                </div>
              ) : (
                <>
                  <table className="stock-table">
                    <thead>
                      <tr>
                        <th>종목코드</th>
                        <th>종목명</th>
                        <th className="hide-on-mobile">DART 코드</th>
                        <th>시장</th>
                        <th className="hide-on-tablet">소속그룹</th>
                        <th className="hide-on-mobile">주요 업종</th>
                        <th className="hide-on-tablet">최초 상장일</th>
                        <th className="hide-on-mobile-xs" style={{ textAlign: 'right' }}>총 상장 주식 수</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stocks.map((stock) => (
                        <tr 
                          key={stock.stock_code} 
                          className="clickable-row" 
                          onClick={() => handleStockClick(stock)}
                        >
                          <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--color-primary)' }}>
                            {stock.stock_code}
                          </td>
                          <td style={{ fontWeight: 600 }}>{stock.stock_name}</td>
                          <td className="hide-on-mobile" style={{ fontFamily: 'monospace', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            {stock.dart_corp_code || '-'}
                          </td>
                          <td>
                            <span className={`market-badge ${stock.market.toLowerCase()}`}>
                              {stock.market}
                            </span>
                          </td>
                          <td className="hide-on-tablet" style={{ color: 'var(--text-secondary)' }}>{stock.security_group || '-'}</td>
                          <td className="hide-on-mobile" style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{stock.sector || '-'}</td>
                          <td className="hide-on-tablet" style={{ color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{stock.listed_date || '-'}</td>
                          <td className="hide-on-mobile-xs" style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>
                            {stock.listed_shares ? stock.listed_shares.toLocaleString() : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Paging component */}
                  <div className="pagination-container">
                    <div className="pagination-info">
                      총 <strong>{total.toLocaleString()}</strong>개 중 <strong>{(page - 1) * 15 + 1} - {Math.min(page * 15, total)}</strong>번째 표시 중
                    </div>
                    <div className="pagination-buttons">
                      <button 
                        className="page-btn" 
                        onClick={() => setPage(1)} 
                        disabled={page === 1}
                      >
                        맨앞
                      </button>
                      <button 
                        className="page-btn" 
                        onClick={() => setPage(p => Math.max(1, p - 1))} 
                        disabled={page === 1}
                      >
                        이전
                      </button>
                      
                      {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                        let pageNum = page;
                        if (page <= 3) {
                          pageNum = i + 1;
                        } else if (page > pages - 2) {
                          pageNum = pages - 4 + i;
                        } else {
                          pageNum = page - 2 + i;
                        }
                        if (pageNum < 1 || pageNum > pages) return null;
                        
                        return (
                          <button 
                            key={pageNum}
                            className={`page-btn ${page === pageNum ? 'active' : ''}`}
                            onClick={() => setPage(pageNum)}
                          >
                            {pageNum}
                          </button>
                        );
                      })}

                      <button 
                        className="page-btn" 
                        onClick={() => setPage(p => Math.min(pages, p + 1))} 
                        disabled={page === pages}
                      >
                        다음
                      </button>
                      <button 
                        className="page-btn" 
                        onClick={() => setPage(pages)} 
                        disabled={page === pages}
                      >
                        맨뒤
                      </button>
                    </div>
                  </div>
                </>
              )}
            </section>
          </>
        ) : (
          <>
            <header className="header-section">
              <div className="header-title">
                <h1>우수 배당주 평가 순위</h1>
                <p>투자 가치 분석 전략에 따라 점수가 산출된 종목들의 종합 평가 순위를 조회합니다. 항목을 클릭하면 상세 재무 및 차트를 조회할 수 있습니다.</p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {usingFallback && (
                  <span style={{ fontSize: '0.8rem', backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.35rem 0.75rem', borderRadius: '20px', fontWeight: 600 }}>
                    ⚠️ 데모용 오프라인 모드
                  </span>
                )}
                {!usingFallback && (
                  <button
                    id="btn-evaluate"
                    className={`sync-btn evaluate-btn ${evaluating ? 'loading' : ''}`}
                    onClick={handleEvaluate}
                    disabled={evaluating || syncingPrices}
                    title="최신 주가 기준으로 전체 종목 투자 점수를 재계산합니다"
                  >
                    <svg className="sync-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                    </svg>
                    {evaluating ? '점수 계산 중...' : '점수 계산'}
                  </button>
                )}
              </div>
            </header>

            {/* Summary grid */}
            <section className="summary-grid">
              <div className="summary-card">
                <span className="card-title">전체 평가 대상 종목</span>
                <span className="card-value">{rankedTotal.toLocaleString()}개</span>
              </div>
              <div className="summary-card">
                <span className="card-title">추천 배당주 후보 수</span>
                <span className="card-value" style={{ color: 'var(--color-primary)' }}>{candidateCount.toLocaleString()}개</span>
              </div>
              <div className="summary-card">
                <span className="card-title">추천 종목 평균 점수</span>
                <span className="card-value" style={{ color: '#059669' }}>{avgScore}점</span>
              </div>
            </section>

            {/* Filters and Searches */}
            <section className="controls-card">
              <div className="search-filter-row">
                <div className="search-input-wrapper">
                  <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  <input
                    type="text"
                    placeholder="종목명, 종목코드, 업종 검색 후 엔터 또는 조회 버튼..."
                    className="search-input"
                    value={rankedSearch}
                    onChange={(e) => setRankedSearch(e.target.value)}
                    onKeyDown={handleRankedSearchKeyPress}
                  />
                </div>
                
                <select 
                  className="market-select"
                  value={rankedMarket}
                  onChange={(e) => { setRankedMarket(e.target.value); setRankedPage(1); }}
                >
                  <option value="">모든 시장</option>
                  <option value="KOSPI">KOSPI</option>
                  <option value="KOSDAQ">KOSDAQ</option>
                </select>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-secondary)', userSelect: 'none', marginLeft: '0.5rem' }}>
                  <input 
                    type="checkbox" 
                    checked={onlyCandidates} 
                    onChange={(e) => { setOnlyCandidates(e.target.checked); setRankedPage(1); }}
                    style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                  />
                  추천 배당주 후보만 보기
                </label>

                <button 
                  className="page-btn active" 
                  style={{ padding: '0.5rem 1.5rem', borderRadius: '10px', marginLeft: 'auto' }}
                  onClick={handleRankedSearchSubmit}
                >
                  조회
                </button>
              </div>
            </section>

            {/* Table representation */}
            <section className="table-wrapper">
              {loadingRanked ? (
                <div className="loading-wrapper">
                  <div className="spinner"></div>
                  <p>평가 순위 목록을 서버에서 불러오는 중입니다...</p>
                </div>
              ) : errorRanked ? (
                <div className="error-card" style={{ margin: '2rem auto', maxWidth: '400px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.75rem', marginBottom: '0.75rem' }}>{errorRanked}</p>
                  <button className="back-btn" style={{ padding: '0.4rem 1.2rem', fontSize: '0.85rem' }} onClick={fetchRankedStocks}>
                    다시 시도
                  </button>
                </div>
              ) : rankedStocks.length === 0 ? (
                <div className="empty-wrapper">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                  <p>조건을 만족하는 평가 종목이 존재하지 않습니다.</p>
                </div>
              ) : (
                <>
                  <table className="stock-table">
                    <thead>
                      <tr>
                        <th style={{ width: '60px', textAlign: 'center' }}>순위</th>
                        <th>종목코드</th>
                        <th>종목명</th>
                        <th className="hide-on-mobile">시장</th>
                        <th className="hide-on-tablet">주요 업종</th>
                        <th className="hide-on-mobile" style={{ textAlign: 'center' }}>안정성</th>
                        <th className="hide-on-mobile" style={{ textAlign: 'center' }}>성장성</th>
                        <th className="hide-on-mobile" style={{ textAlign: 'center' }}>저평가</th>
                        <th className="hide-on-mobile" style={{ textAlign: 'center' }}>주주환원</th>
                        <th className="hide-on-mobile" style={{ textAlign: 'center' }}>거버넌스</th>
                        <th style={{ textAlign: 'center' }}>종합 점수</th>
                        <th style={{ textAlign: 'center' }}>추천 여부</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rankedStocks.map((stock, index) => {
                        const rank = (rankedPage - 1) * 15 + index + 1;
                        const isHigh = (stock.total_score || 0) >= 70;
                        const isMid = (stock.total_score || 0) >= 60 && (stock.total_score || 0) < 70;
                        const scoreColor = isHigh ? '#10b981' : isMid ? '#f59e0b' : '#9ca3af';
                        
                        const fullStockItem: StockItem = {
                          stock_code: stock.stock_code,
                          stock_name: stock.stock_name,
                          market: stock.market,
                          sector: stock.sector || undefined,
                          is_active: 1
                        };

                        return (
                          <tr 
                            key={stock.stock_code} 
                            className="clickable-row" 
                            onClick={() => handleStockClick(fullStockItem)}
                          >
                            <td style={{ textAlign: 'center', fontWeight: 700, color: rank <= 3 ? 'var(--color-primary)' : 'var(--text-secondary)' }}>
                              {rank}
                            </td>
                            <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--color-primary)' }}>
                              {stock.stock_code}
                            </td>
                            <td style={{ fontWeight: 600 }}>{stock.stock_name}</td>
                            <td className="hide-on-mobile">
                              <span className={`market-badge ${stock.market.toLowerCase()}`}>
                                {stock.market}
                              </span>
                            </td>
                            <td className="hide-on-tablet" style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{stock.sector || '-'}</td>
                            <td className="hide-on-mobile" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                              {stock.financial_stability_score !== null && stock.financial_stability_score !== undefined ? `${stock.financial_stability_score}점` : '-'}
                            </td>
                            <td className="hide-on-mobile" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                              {stock.growth_score !== null && stock.growth_score !== undefined ? `${stock.growth_score}점` : '-'}
                            </td>
                            <td className="hide-on-mobile" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                              {stock.undervaluation_score !== null && stock.undervaluation_score !== undefined ? `${stock.undervaluation_score}점` : '-'}
                            </td>
                            <td className="hide-on-mobile" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                              {stock.shareholder_return_score !== null && stock.shareholder_return_score !== undefined ? `${stock.shareholder_return_score}점` : '-'}
                            </td>
                            <td className="hide-on-mobile" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                              {stock.market_governance_score !== null && stock.market_governance_score !== undefined ? `${stock.market_governance_score}점` : '-'}
                            </td>
                            <td style={{ textAlign: 'center', fontWeight: 700, color: scoreColor, fontSize: '1.05rem' }}>
                              {stock.total_score !== null && stock.total_score !== undefined ? `${stock.total_score}점` : '-'}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              {stock.is_candidate === 1 ? (
                                <span style={{ fontSize: '0.75rem', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
                                  🌟 추천
                                </span>
                              ) : (
                                <span style={{ fontSize: '0.75rem', backgroundColor: '#f3f4f6', color: '#9ca3af', padding: '0.25rem 0.5rem', borderRadius: '4px', fontWeight: 500 }}>
                                  제외
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>

                  {/* Paging component */}
                  <div className="pagination-container">
                    <div className="pagination-info">
                      총 <strong>{rankedTotal.toLocaleString()}</strong>개 중 <strong>{(rankedPage - 1) * 15 + 1} - {Math.min(rankedPage * 15, rankedTotal)}</strong>번째 표시 중
                    </div>
                    <div className="pagination-buttons">
                      <button 
                        className="page-btn" 
                        onClick={() => setRankedPage(1)} 
                        disabled={rankedPage === 1}
                      >
                        맨앞
                      </button>
                      <button 
                        className="page-btn" 
                        onClick={() => setRankedPage(p => Math.max(1, p - 1))} 
                        disabled={rankedPage === 1}
                      >
                        이전
                      </button>
                      
                      {Array.from({ length: Math.min(5, rankedPages) }, (_, i) => {
                        let pageNum = rankedPage;
                        if (rankedPage <= 3) {
                          pageNum = i + 1;
                        } else if (rankedPage > rankedPages - 2) {
                          pageNum = rankedPages - 4 + i;
                        } else {
                          pageNum = rankedPage - 2 + i;
                        }
                        if (pageNum < 1 || pageNum > rankedPages) return null;
                        
                        return (
                          <button 
                            key={pageNum}
                            className={`page-btn ${rankedPage === pageNum ? 'active' : ''}`}
                            onClick={() => setRankedPage(pageNum)}
                          >
                            {pageNum}
                          </button>
                        );
                      })}

                      <button 
                        className="page-btn" 
                        onClick={() => setRankedPage(p => Math.min(rankedPages, p + 1))} 
                        disabled={rankedPage === rankedPages}
                      >
                        다음
                      </button>
                      <button 
                        className="page-btn" 
                        onClick={() => setRankedPage(rankedPages)} 
                        disabled={rankedPage === rankedPages}
                      >
                        맨뒤
                      </button>
                    </div>
                  </div>
                </>
              )}
            </section>
          </>
        )}
      </main>

      {showDetailsModal && evaluation && (
        <ScoreDetailsOverlay 
          evaluation={evaluation} 
          onClose={() => setShowDetailsModal(false)} 
        />
      )}
    </div>
  );
}

// ----------------------------------------------------
// 🔍 ScoreDetailsOverlay Component (Detailed Score Calculations)
// ----------------------------------------------------
interface ScoreDetailsOverlayProps {
  evaluation: StockEvaluationItem;
  onClose: () => void;
}

function ScoreDetailsOverlay({ evaluation, onClose }: ScoreDetailsOverlayProps) {
  // Helper to ensure values are safe numbers
  const safeNum = (v: any): number | null => {
    if (v === undefined || v === null || v === '') return null;
    const n = Number(v);
    return isNaN(n) ? null : n;
  };

  const debtVal = safeNum(evaluation.debt_ratio);
  const currentVal = safeNum(evaluation.current_ratio);
  const revenueVal = safeNum(evaluation.revenue_growth);
  const opVal = safeNum(evaluation.operating_income_growth);
  const epsVal = safeNum(evaluation.eps_growth);
  const perVal = safeNum(evaluation.per);
  const pbrVal = safeNum(evaluation.pbr);
  const payoutVal = safeNum(evaluation.payout_ratio);
  const divYearsVal = safeNum(evaluation.dividend_years);
  const decreaseCountVal = safeNum(evaluation.dividend_decrease_count) || 0;

  // 1. 재무 안정성 점수 세부 연산
  const getDebtRatioScore = (val: number | null) => {
    if (val === null) return { score: 0, desc: "데이터 없음 (0점)" };
    if (val <= 50) return { score: 8, desc: `${val.toFixed(2)}% ≤ 50% (8점 만점)` };
    if (val <= 100) return { score: 6, desc: `${val.toFixed(2)}% ≤ 100% (6점)` };
    if (val <= 200) return { score: 4, desc: `${val.toFixed(2)}% ≤ 200% (4점)` };
    if (val <= 400) return { score: 2, desc: `${val.toFixed(2)}% ≤ 400% (2점)` };
    return { score: 0, desc: `${val.toFixed(2)}% > 400% 초과 (0점)` };
  };

  const getCurrentRatioScore = (val: number | null) => {
    if (val === null) return { score: 0, desc: "데이터 없음 (0점)" };
    if (val >= 200) return { score: 7, desc: `${val.toFixed(2)}% ≥ 200% (7점 만점)` };
    if (val >= 150) return { score: 5, desc: `${val.toFixed(2)}% ≥ 150% (5점)` };
    if (val >= 100) return { score: 3, desc: `${val.toFixed(2)}% ≥ 100% (3점)` };
    return { score: 0, desc: `${val.toFixed(2)}% < 100% 미만 (0점)` };
  };

  // 2. 성장성 점수 세부 연산
  const getRevenueGrowthScore = (val: number | null) => {
    if (val === null) return { score: 0, desc: "데이터 없음 (0점)" };
    if (val >= 10) return { score: 5, desc: `${val.toFixed(2)}% ≥ 10% (5점 만점)` };
    if (val >= 5) return { score: 4, desc: `${val.toFixed(2)}% ≥ 5% (4점)` };
    if (val >= 0) return { score: 2, desc: `${val.toFixed(2)}% ≥ 0% (2점)` };
    return { score: 0, desc: `${val.toFixed(2)}% < 0% 역성장 (0점)` };
  };

  const getOperatingIncomeGrowthScore = (val: number | null) => {
    if (val === null) return { score: 0, desc: "데이터 없음 (0점)" };
    if (val >= 15) return { score: 5, desc: `${val.toFixed(2)}% ≥ 15% (5점 만점)` };
    if (val >= 5) return { score: 4, desc: `${val.toFixed(2)}% ≥ 5% (4점)` };
    if (val >= 0) return { score: 2, desc: `${val.toFixed(2)}% ≥ 0% (2점)` };
    return { score: 0, desc: `${val.toFixed(2)}% < 0% 역성장 (0점)` };
  };

  const getEpsGrowthScore = (val: number | null) => {
    if (val === null) return { score: 0, desc: "데이터 없음 (0점)" };
    if (val >= 15) return { score: 5, desc: `${val.toFixed(2)}% ≥ 15% (5점 만점)` };
    if (val >= 5) return { score: 4, desc: `${val.toFixed(2)}% ≥ 5% (4점)` };
    if (val >= 0) return { score: 2, desc: `${val.toFixed(2)}% ≥ 0% (2점)` };
    return { score: 0, desc: `${val.toFixed(2)}% < 0% 역성장 (0점)` };
  };

  // 3. 저평가 점수 세부 연산
  const getPerScore = (val: number | null) => {
    if (val === null || val <= 0) return { score: 0, desc: "데이터 없음/적자 (0점)" };
    if (val <= 6) return { score: 15, desc: `${val.toFixed(2)}배 ≤ 6배 (15점 만점)` };
    if (val <= 10) return { score: 12, desc: `${val.toFixed(2)}배 ≤ 10배 (12점)` };
    if (val <= 15) return { score: 8, desc: `${val.toFixed(2)}배 ≤ 15배 (8점)` };
    if (val <= 25) return { score: 4, desc: `${val.toFixed(2)}배 ≤ 25배 (4점)` };
    return { score: 0, desc: `${val.toFixed(2)}배 > 25배 초과 (0점)` };
  };

  const getPbrScore = (val: number | null) => {
    if (val === null || val <= 0) return { score: 0, desc: "데이터 없음 (0점)" };
    if (val <= 0.6) return { score: 15, desc: `${val.toFixed(2)}배 ≤ 0.6배 (15점 만점)` };
    if (val <= 1.0) return { score: 12, desc: `${val.toFixed(2)}배 ≤ 1.0배 (12점)` };
    if (val <= 1.5) return { score: 8, desc: `${val.toFixed(2)}배 ≤ 1.5배 (8점)` };
    if (val <= 2.5) return { score: 4, desc: `${val.toFixed(2)}배 ≤ 2.5배 (4점)` };
    return { score: 0, desc: `${val.toFixed(2)}배 > 2.5배 (0점)` };
  };

  // 4. 주주환원 점수 세부 연산
  const getPayoutScore = (val: number | null) => {
    if (val === null || val <= 0) return { score: 0, desc: "데이터 없음 (0점)" };
    const pct = val; // API에서 이미 백분율(%) 수치로 제공됨
    if (pct >= 20 && pct <= 60) return { score: 15, desc: `${pct.toFixed(2)}% (20% ~ 60% 최적 구간, 15점 만점)` };
    if (pct >= 10 && pct <= 80) return { score: 10, desc: `${pct.toFixed(2)}% (10% ~ 80% 완만 구간, 10점)` };
    return { score: 5, desc: `${pct.toFixed(2)}% (소극 환원 혹은 무리한 배당, 5점)` };
  };

  const getDividendYearsScore = (val: number | null) => {
    if (val === null || val === 0) return { score: 0, desc: "배당 없음 (0점)" };
    if (val >= 3) return { score: 15, desc: `${val}년 연속 지급 ≥ 3년 (15점 만점)` };
    if (val === 2) return { score: 10, desc: `2년 연속 지급 (10점)` };
    if (val === 1) return { score: 5, desc: `1년 연속 (당해 첫 배당, 5점)` };
    return { score: 0, desc: "데이터 없음 (0점)" };
  };

  const debtInfo = getDebtRatioScore(debtVal);
  const currentInfo = getCurrentRatioScore(currentVal);
  const stabilitySum = Math.min(debtInfo.score + currentInfo.score, 15);

  const revInfo = getRevenueGrowthScore(revenueVal);
  const opInfo = getOperatingIncomeGrowthScore(opVal);
  const epsGrowthInfo = getEpsGrowthScore(epsVal);
  const growthSum = Math.min(revInfo.score + opInfo.score + epsGrowthInfo.score, 15);

  const perInfo = getPerScore(perVal);
  const pbrInfo = getPbrScore(pbrVal);
  const valuationSum = Math.min(perInfo.score + pbrInfo.score, 25);

  const payoutInfo = getPayoutScore(payoutVal);
  const divYearsInfo = getDividendYearsScore(divYearsVal);
  const decreasePenalty = Math.min(decreaseCountVal * 5, 15);
  const shareholderSum = Math.max(Math.min(payoutInfo.score + divYearsInfo.score - decreasePenalty, 25), 0);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📊 상세 투자 점수 산출 내역서</h2>
          <button className="modal-close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <p className="modal-desc">
            현재 <strong>100점 만점 5대 투자 분석 모델</strong>을 기준으로 계산된 부문별 세부 취득 점수와 평가 대조 내역입니다.
          </p>

          <div className="breakdown-grid">
            {/* 부문 1: 안정성 */}
            <div className="breakdown-section">
              <div className="section-header color-stability">
                <span>① 금융 재무 안정성</span>
                <span className="section-total">{stabilitySum} / 15점</span>
              </div>
              <div className="section-body">
                <div className="indicator-row">
                  <span className="ind-name">부채비율 (배점 8점)</span>
                  <span className="ind-val">{debtInfo.desc}</span>
                </div>
                <div className="indicator-row">
                  <span className="ind-name">유동비율 (배점 7점)</span>
                  <span className="ind-val">{currentInfo.desc}</span>
                </div>
              </div>
            </div>

            {/* 부문 2: 성장성 */}
            <div className="breakdown-section">
              <div className="section-header color-growth">
                <span>② 본업 지속 성장성</span>
                <span className="section-total">{growthSum} / 15점</span>
              </div>
              <div className="section-body">
                <div className="indicator-row">
                  <span className="ind-name">매출액 성장률 (배점 5점)</span>
                  <span className="ind-val">{revInfo.desc}</span>
                </div>
                <div className="indicator-row">
                  <span className="ind-name">영업이익 성장률 (배점 5점)</span>
                  <span className="ind-val">{opInfo.desc}</span>
                </div>
                <div className="indicator-row">
                  <span className="ind-name">EPS 성장률 (배점 5점)</span>
                  <span className="ind-val">{epsGrowthInfo.desc}</span>
                </div>
              </div>
            </div>

            {/* 부문 3: 저평가 */}
            <div className="breakdown-section">
              <div className="section-header color-undervaluation">
                <span>③ 가격 매력도 및 저평가 (밸류에이션)</span>
                <span className="section-total">{valuationSum} / 25점</span>
              </div>
              <div className="section-body">
                <div className="indicator-row">
                  <span className="ind-name">PER (배점 15점)</span>
                  <span className="ind-val">{perInfo.desc}</span>
                </div>
                <div className="indicator-row">
                  <span className="ind-name">PBR (배점 15점)</span>
                  <span className="ind-val">{pbrInfo.desc}</span>
                </div>
                <div className="indicator-footer">
                  * PER과 PBR 점수의 합계에 25점 상한 캡(Cap)을 적용합니다. (합산: {perInfo.score + pbrInfo.score}점)
                </div>
              </div>
            </div>

            {/* 부문 4: 주주환원 */}
            <div className="breakdown-section">
              <div className="section-header color-return">
                <span>④ 주주 환원 및 배당 매력</span>
                <span className="section-total">{shareholderSum} / 25점</span>
              </div>
              <div className="section-body">
                <div className="indicator-row">
                  <span className="ind-name">배당 성향 (배점 15점)</span>
                  <span className="ind-val">{payoutInfo.desc}</span>
                </div>
                <div className="indicator-row">
                  <span className="ind-name">배당 지속 연수 (배점 15점)</span>
                  <span className="ind-val">{divYearsInfo.desc}</span>
                </div>
                {decreasePenalty > 0 && (
                  <div className="indicator-row penalty">
                    <span className="ind-name">배당 삭감 이력 (감점)</span>
                    <span className="ind-val" style={{ color: 'var(--color-danger)', fontWeight: 'bold' }}>
                      -{decreasePenalty}점 감점 (삭감 횟수: {evaluation.dividend_decrease_count}회)
                    </span>
                  </div>
                )}
                <div className="indicator-footer">
                  * (배당성향 + 배당지속 + 자사주가점 - 삭감감점)에 최소 0점 ~ 최대 25점 한도를 적용합니다.
                </div>
              </div>
            </div>

            {/* 부문 5: 거버넌스 */}
            <div className="breakdown-section">
              <div className="section-header color-governance">
                <span>⑤ 시장 및 지배구조 리스크 (거버넌스)</span>
                <span className="section-total">0 / 20점</span>
              </div>
              <div className="section-body">
                <div className="indicator-footer" style={{ marginTop: 0, fontSize: '0.85rem' }}>
                  현재 거버넌스 지표는 1차 0점 고정 상태입니다. 향후 정성적 공시 요약 및 지배구조 데이터, LLM 분석 모듈을 보강하여 최대 20점 한도로 실데이터를 연동할 예정입니다.
                </div>
              </div>
            </div>
          </div>

          <div className="modal-total-summary">
            <span>종합 투자 점수 합산:</span>
            <strong className="summary-score">{evaluation.total_score !== undefined && evaluation.total_score !== null ? Math.round(evaluation.total_score) : '-'} / 100점</strong>
          </div>
        </div>

        <div className="modal-footer">
          <button className="back-btn" onClick={onClose} style={{ padding: '0.6rem 1.5rem', fontWeight: 600 }}>
            확인 및 닫기
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
