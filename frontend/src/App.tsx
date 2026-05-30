import { useState, useEffect } from 'react';
import './App.css';

interface StockItem {
  stock_code: string;
  stock_name: string;
  market: string;
  security_group?: string;
  sector?: string;
  listed_date?: string;
  listed_shares?: number;
  is_active: number;
}

// 10 mock items for fallback (just in case backend is offline)
const MOCK_STOCKS: StockItem[] = [
  { stock_code: "005930", stock_name: "삼성전자", market: "KOSPI", security_group: "주식", sector: "반도체 및 관련장비 제조업", listed_date: "1975-06-11", listed_shares: 5969782550, is_active: 1 },
  { stock_code: "000660", stock_name: "SK하이닉스", market: "KOSPI", security_group: "주식", sector: "반도체 및 관련장비 제조업", listed_date: "1996-12-26", listed_shares: 728002365, is_active: 1 },
  { stock_code: "035420", stock_name: "NAVER", market: "KOSPI", security_group: "주식", sector: "자료처리, 호스팅, 포털 및 기타 인터넷 정보매개 서비스업", listed_date: "2002-10-29", listed_shares: 162408573, is_active: 1 },
  { stock_code: "035720", stock_name: "카카오", market: "KOSPI", security_group: "주식", sector: "자료처리, 호스팅, 포털 및 기타 인터넷 정보매개 서비스업", listed_date: "1999-11-11", listed_shares: 443522071, is_active: 1 },
  { stock_code: "207940", stock_name: "삼성바이오로직스", market: "KOSPI", security_group: "주식", sector: "기초 의약물질 및 생물학적 제제 제조업", listed_date: "2016-11-10", listed_shares: 71174000, is_active: 1 },
  { stock_code: "005380", stock_name: "현대자동차", market: "KOSPI", security_group: "주식", sector: "자동차용 엔진 및 자동차 제조업", listed_date: "1974-06-28", listed_shares: 211531506, is_active: 1 },
  { stock_code: "005490", stock_name: "POSCO홀딩스", market: "KOSPI", security_group: "주식", sector: "1차 철강 제조업", listed_date: "1988-06-10", listed_shares: 84571230, is_active: 1 },
  { stock_code: "091990", stock_name: "셀트리온제약", market: "KOSDAQ", security_group: "주식", sector: "의약품 제조업", listed_date: "2017-07-28", listed_shares: 165007421, is_active: 1 },
  { stock_code: "293490", stock_name: "카카오게임즈", market: "KOSDAQ", security_group: "주식", sector: "소프트웨어 개발 및 공급업", listed_date: "2020-09-10", listed_shares: 82348398, is_active: 1 },
  { stock_code: "003670", stock_name: "포스코퓨처엠", market: "KOSPI", security_group: "주식", sector: "기타 화학제품 제조업", listed_date: "2001-10-19", listed_shares: 77463270, is_active: 1 }
];

function App() {
  const [stocks, setStocks] = useState<StockItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState('');
  const [market, setMarket] = useState('');
  const [loading, setLoading] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);

  const fetchStocks = async () => {
    setLoading(true);
    setUsingFallback(false);

    const pageSize = 15;
    const params = new URLSearchParams({
      page: page.toString(),
      size: pageSize.toString(),
    });
    if (search.trim()) params.append('search', search);
    if (market) params.append('market', market);

    try {
      const response = await fetch(`http://localhost:8000/api/stocks?${params.toString()}`);
      if (!response.ok) {
        throw new Error('API server returned error');
      }
      const data = await response.json();
      setStocks(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      console.warn("Backend API is offline or failed. Using fallback mock data. Error: ", err);
      setUsingFallback(true);
      
      // Fallback local search & filter logic
      let filtered = [...MOCK_STOCKS];
      if (market) {
        filtered = filtered.filter(s => s.market === market);
      }
      if (search.trim()) {
        const query = search.toLowerCase();
        filtered = filtered.filter(s => 
          s.stock_code.includes(query) || 
          s.stock_name.toLowerCase().includes(query) || 
          (s.sector && s.sector.toLowerCase().includes(query))
        );
      }

      const totalCount = filtered.length;
      const totalPages = Math.ceil(totalCount / pageSize) || 1;
      const startIndex = (page - 1) * pageSize;
      const paginated = filtered.slice(startIndex, startIndex + pageSize);

      setStocks(paginated);
      setTotal(totalCount);
      setPages(totalPages);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, [page, market]);

  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      setPage(1);
      fetchStocks();
    }
  };

  const handleSearchSubmit = () => {
    setPage(1);
    fetchStocks();
  };

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
            <li className="nav-item active">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
              종목 조회
            </li>
            <li className="nav-item">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
              배당주 분석 (준비중)
            </li>
            <li className="nav-item">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              가상 테스트 (준비중)
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header-section">
          <div className="header-title">
            <h1>전체 상장 종목 조회</h1>
            <p>한국거래소(KRX)에 등록된 전체 활성 종목들의 실시간 목록을 조회합니다.</p>
          </div>
          {usingFallback && (
            <span style={{ fontSize: '0.8rem', backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.35rem 0.75rem', borderRadius: '20px', fontWeight: 600 }}>
              ⚠️ 데모용 오프라인 모드
            </span>
          )}
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
            <div className="search-input-wrapper">
              <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input
                type="text"
                placeholder="종목명, 종목코드, 업종 검색 후 엔터 또는 조회 버튼..."
                className="search-input"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={handleSearchKeyPress}
              />
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
                    <th>시장</th>
                    <th>소속그룹</th>
                    <th>주요 업종</th>
                    <th>최초 상장일</th>
                    <th style={{ textAlign: 'right' }}>총 상장 주식 수</th>
                  </tr>
                </thead>
                <tbody>
                  {stocks.map((stock) => (
                    <tr key={stock.stock_code}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--color-primary)' }}>
                        {stock.stock_code}
                      </td>
                      <td style={{ fontWeight: 600 }}>{stock.stock_name}</td>
                      <td>
                        <span className={`market-badge ${stock.market.toLowerCase()}`}>
                          {stock.market}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{stock.security_group || '-'}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{stock.sector || '-'}</td>
                      <td style={{ color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{stock.listed_date || '-'}</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>
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
      </main>
    </div>
  );
}

export default App;
