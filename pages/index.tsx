import { useEffect, useState } from 'react';
import Head from 'next/head';
import styles from '../styles/Home.module.css';

interface Signal {
  stockCode: string;
  currentPrice: number;
  change?: number;
  changePercent?: number;
  volume?: number;
  high?: number;
  low?: number;
  signal: string;
  signalType: string;
  score: number;
  probability: number;
  analysis: string;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  maxDrawdown: number;
  positionSize: number;
  timestamp: string;
  dataSource?: string;
}

interface RiskAnalysis {
  marketSentiment: string;
  fearIndex: number;
  stopTradingMode: boolean;
  alerts: Array<{
    type: string;
    title: string;
    message: string;
  }>;
  explanation: string;
  recommendations: string[];
}

interface DisciplineAnalysis {
  emotionDetected: string;
  emotionScore: number;
  intervention: boolean;
  message: string;
  advice: string[];
  behaviorInsights?: {
    chasedBuys: number;
    panicSells: number;
    disciplineScore: number;
    trend: string;
  };
}

interface VIPRegistration {
  name: string;
  email: string;
  phone: string;
  registeredAt: string;
}

export default function Home() {
  const [buySignals, setBuySignals] = useState<Signal[]>([]);
  const [sellSignals, setSellSignals] = useState<Signal[]>([]);
  const [riskAnalysis, setRiskAnalysis] = useState<RiskAnalysis | null>(null);
  const [disciplineAnalysis, setDisciplineAnalysis] = useState<DisciplineAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('signals');
  const [userMessage, setUserMessage] = useState('');
  
  // VIP popup state
  const [showVIPPopup, setShowVIPPopup] = useState(false);
  const [vipRegistered, setVIPRegistered] = useState(false);
  const [vipForm, setVIPForm] = useState({
    name: '',
    email: '',
    phone: ''
  });

  useEffect(() => {
    // Check if user already registered
    const registration = localStorage.getItem('vip_registration');
    if (registration) {
      setVIPRegistered(true);
    }
    
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    
    try {
      // Load AI signals
      const signalsRes = await fetch('/api/signals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysisType: 'all' })
      });
      const signalsData = await signalsRes.json();
      
      const buys = signalsData.signals.filter((s: Signal) => s.signal === 'MUA');
      const sells = signalsData.signals.filter((s: Signal) => s.signal === 'BÁN');
      
      setBuySignals(buys);
      setSellSignals(sells);

      // Load risk analysis
      const riskRes = await fetch('/api/risk-analysis');
      const riskData = await riskRes.json();
      setRiskAnalysis(riskData);

      // Load discipline analysis
      const disciplineRes = await fetch('/api/discipline-coach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userBehavior: {
            chasedBuys: 8,
            panicSells: 3,
            disciplineScore: 72
          }
        })
      });
      const disciplineData = await disciplineRes.json();
      setDisciplineAnalysis(disciplineData);

    } catch (error) {
      console.error('Error loading data:', error);
    }
    
    setLoading(false);
  };

  const handleVIPTabClick = (tab: string) => {
    if ((tab === 'risk' || tab === 'discipline') && !vipRegistered) {
      setShowVIPPopup(true);
      return;
    }
    setActiveTab(tab);
  };

  const handleVIPSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!vipForm.name || !vipForm.email) {
      alert('Vui lòng điền Họ tên và Email');
      return;
    }

    const registration: VIPRegistration = {
      ...vipForm,
      registeredAt: new Date().toISOString()
    };

    // Save to localStorage
    localStorage.setItem('vip_registration', JSON.stringify(registration));
    
    // Close popup and allow access
    setVIPRegistered(true);
    setShowVIPPopup(false);
    
    // Show success message
    alert('🎉 Đăng ký thành công! Chào mừng bạn đến với VIP features!');
  };

  const askDisciplineCoach = async () => {
    if (!userMessage.trim()) return;

    try {
      const res = await fetch('/api/discipline-coach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userMessage })
      });
      const data = await res.json();
      setDisciplineAnalysis(data);
      setUserMessage('');
    } catch (error) {
      console.error('Error asking coach:', error);
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>AI Advisor - Investment Assistant</title>
        <meta name="description" content="AI-powered investment advisor" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>🤖</span>
            <span className={styles.logoText}>AI Advisor</span>
          </div>
          <div className={styles.badge}>
            {vipRegistered ? '✨ VIP Member' : 'FREE'}
          </div>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.tabs}>
          <button 
            className={activeTab === 'signals' ? styles.tabActive : styles.tab}
            onClick={() => setActiveTab('signals')}
          >
            🎯 Tín hiệu AI
          </button>
          <button 
            className={activeTab === 'risk' ? styles.tabActive : styles.tab}
            onClick={() => handleVIPTabClick('risk')}
          >
            🛡️ Risk Shield {!vipRegistered && '🔒'}
          </button>
          <button 
            className={activeTab === 'discipline' ? styles.tabActive : styles.tab}
            onClick={() => handleVIPTabClick('discipline')}
          >
            🧠 Discipline Coach {!vipRegistered && '🔒'}
          </button>
        </div>

        {/* VIP Registration Popup */}
        {showVIPPopup && (
          <div className={styles.popupOverlay} onClick={() => setShowVIPPopup(false)}>
            <div className={styles.popupContent} onClick={(e) => e.stopPropagation()}>
              <button className={styles.popupClose} onClick={() => setShowVIPPopup(false)}>
                ✕
              </button>
              
              <div className={styles.popupHeader}>
                <span className={styles.popupIcon}>🎁</span>
                <h2>Đăng ký để xem VIP Features</h2>
                <p>Truy cập AI Risk Shield & Discipline Coach miễn phí!</p>
              </div>

              <form onSubmit={handleVIPSubmit} className={styles.vipForm}>
                <div className={styles.formGroup}>
                  <label>Họ và tên *</label>
                  <input
                    type="text"
                    value={vipForm.name}
                    onChange={(e) => setVIPForm({...vipForm, name: e.target.value})}
                    placeholder="Nguyễn Văn A"
                    required
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>Email *</label>
                  <input
                    type="email"
                    value={vipForm.email}
                    onChange={(e) => setVIPForm({...vipForm, email: e.target.value})}
                    placeholder="email@example.com"
                    required
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>Số điện thoại</label>
                  <input
                    type="tel"
                    value={vipForm.phone}
                    onChange={(e) => setVIPForm({...vipForm, phone: e.target.value})}
                    placeholder="0901234567"
                  />
                </div>

                <div className={styles.formButtons}>
                  <button type="button" className={styles.btnSecondary} onClick={() => setShowVIPPopup(false)}>
                    Để sau
                  </button>
                  <button type="submit" className={styles.btnPrimary}>
                    Xem ngay ✨
                  </button>
                </div>
              </form>

              <div className={styles.popupFooter}>
                <p>✅ Hoàn toàn miễn phí</p>
                <p>✅ Không cần thẻ tín dụng</p>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Đang phân tích với AI...</p>
          </div>
        ) : (
          <>
            {activeTab === 'signals' && (
              <div className={styles.section}>
                <h2 className={styles.sectionTitle}>🟢 Tín hiệu MUA</h2>
                <div className={styles.signalsGrid}>
                  {buySignals.map((signal, idx) => (
                    <div key={idx} className={styles.signalCard}>
                      <div className={styles.signalHeader}>
                        <span className={styles.stockCode}>{signal.stockCode}</span>
                        <span className={styles.signalBadgeBuy}>{signal.signalType}</span>
                      </div>
                      <div className={styles.signalTimestamp}>
                        {new Date(signal.timestamp).toLocaleString('vi-VN', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                      <div className={styles.signalPrice}>
                        {signal.currentPrice.toLocaleString('vi-VN')} VND
                        {signal.changePercent !== undefined && (
                          <span style={{
                            fontSize: '14px',
                            marginLeft: '8px',
                            color: signal.changePercent > 0 ? '#10b981' : '#ef4444'
                          }}>
                            {signal.changePercent > 0 ? '+' : ''}{signal.changePercent}%
                          </span>
                        )}
                      </div>
                      {signal.volume && (
                        <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                          KL: {(signal.volume / 1000000).toFixed(2)}M | 
                          Cao: {signal.high?.toLocaleString()} | 
                          Thấp: {signal.low?.toLocaleString()}
                        </div>
                      )}
                      <div className={styles.signalMetrics}>
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Score</span>
                          <span className={styles.metricValue}>{signal.score}/100</span>
                        </div>
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Xác suất</span>
                          <span className={styles.metricValue}>{signal.probability}%</span>
                        </div>
                      </div>
                      <div className={styles.signalAnalysis}>
                        {signal.analysis}
                      </div>
                      <div className={styles.signalDetails}>
                        <div className={styles.detailRow}>
                          <span>Entry:</span>
                          <span>{signal.entryPrice.toLocaleString()}</span>
                        </div>
                        <div className={styles.detailRow}>
                          <span>Stop Loss:</span>
                          <span className={styles.danger}>{signal.stopLoss.toLocaleString()}</span>
                        </div>
                        <div className={styles.detailRow}>
                          <span>Take Profit:</span>
                          <span className={styles.success}>{signal.takeProfit.toLocaleString()}</span>
                        </div>
                        <div className={styles.detailRow}>
                          <span>Position Size:</span>
                          <span>{signal.positionSize}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <h2 className={styles.sectionTitle} style={{marginTop: '48px'}}>🔴 Tín hiệu BÁN</h2>
                <div className={styles.signalsGrid}>
                  {sellSignals.map((signal, idx) => (
                    <div key={idx} className={styles.signalCard}>
                      <div className={styles.signalHeader}>
                        <span className={styles.stockCode}>{signal.stockCode}</span>
                        <span className={styles.signalBadgeSell}>{signal.signalType}</span>
                      </div>
                      <div className={styles.signalTimestamp}>
                        {new Date(signal.timestamp).toLocaleString('vi-VN', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                      <div className={styles.signalPrice}>
                        {signal.currentPrice.toLocaleString('vi-VN')} VND
                        {signal.changePercent !== undefined && (
                          <span style={{
                            fontSize: '14px',
                            marginLeft: '8px',
                            color: signal.changePercent > 0 ? '#10b981' : '#ef4444'
                          }}>
                            {signal.changePercent > 0 ? '+' : ''}{signal.changePercent}%
                          </span>
                        )}
                      </div>
                      {signal.volume && (
                        <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                          KL: {(signal.volume / 1000000).toFixed(2)}M | 
                          Cao: {signal.high?.toLocaleString()} | 
                          Thấp: {signal.low?.toLocaleString()}
                        </div>
                      )}
                      <div className={styles.signalMetrics}>
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Score</span>
                          <span className={styles.metricValue}>{signal.score}/100</span>
                        </div>
                        <div className={styles.metric}>
                          <span className={styles.metricLabel}>Xác suất</span>
                          <span className={styles.metricValue}>{signal.probability}%</span>
                        </div>
                      </div>
                      <div className={styles.signalAnalysis}>
                        {signal.analysis}
                      </div>
                    </div>
                  ))}
                </div>

                <button onClick={loadData} className={styles.refreshButton}>
                  🔄 Làm mới tín hiệu
                </button>

                {/* Lịch sử khuyến nghị */}
                <div className={styles.historySection}>
                  <h2 className={styles.sectionTitle}>📊 Lịch sử khuyến nghị</h2>
                  <div className={styles.historyTable}>
                    <div className={styles.historyHeader}>
                      <span>Ngày mua</span>
                      <span>Mã</span>
                      <span>Tín hiệu</span>
                      <span>Score</span>
                      <span>Giá mua</span>
                      <span>Ngày bán</span>
                      <span>Giá bán</span>
                      <span>P/L (%)</span>
                      <span>Số ngày giữ</span>
                    </div>

                    {/* SAB - Closed */}
                    <div className={styles.historyRow}>
                      <span>12/01/2025</span>
                      <span className={styles.historyCode}>SAB</span>
                      <span>Swing T+</span>
                      <span>70</span>
                      <span>48,700</span>
                      <span>12/10/2025</span>
                      <span>51,700</span>
                      <span className={styles.profitPositive}>+6.16%</span>
                      <span>10</span>
                    </div>

                    {/* GAS - Closed */}
                    <div className={styles.historyRow}>
                      <span>12/01/2025</span>
                      <span className={styles.historyCode}>GAS</span>
                      <span>Swing T+</span>
                      <span>65</span>
                      <span>64,100</span>
                      <span>08/12/2025</span>
                      <span>64,700</span>
                      <span className={styles.profitPositive}>+0.94%</span>
                      <span>7</span>
                    </div>

                    {/* HAG - Holding */}
                    <div className={styles.historyRow}>
                      <span>04/12/2025</span>
                      <span className={styles.historyCode}>HAG</span>
                      <span>Swing T+</span>
                      <span>60</span>
                      <span>18,400</span>
                      <span className={styles.holdingLabel}>Đang giữ</span>
                      <span>-</span>
                      <span className={styles.profitNegative}>-2.0%</span>
                      <span>-</span>
                    </div>

                    {/* BMP - Holding */}
                    <div className={styles.historyRow}>
                      <span>11/12/2025</span>
                      <span className={styles.historyCode}>BMP</span>
                      <span>Trend Following</span>
                      <span>68</span>
                      <span>165,000</span>
                      <span className={styles.holdingLabel}>Đang giữ</span>
                      <span>-</span>
                      <span className={styles.profitPositive}>+5.0%</span>
                      <span>-</span>
                    </div>

                    {/* VNM - Holding */}
                    <div className={styles.historyRow}>
                      <span>15/12/2025</span>
                      <span className={styles.historyCode}>VNM</span>
                      <span>Trend Following</span>
                      <span>72</span>
                      <span>61,200</span>
                      <span className={styles.holdingLabel}>Đang giữ</span>
                      <span>-</span>
                      <span className={styles.profitPositive}>+3.5%</span>
                      <span>-</span>
                    </div>
                  </div>

                  <div className={styles.historySummary}>
                    <div className={styles.summaryCard}>
                      <span>Tổng lệnh:</span>
                      <strong>5</strong>
                    </div>
                    <div className={styles.summaryCard}>
                      <span>Đã chốt:</span>
                      <strong>2</strong>
                    </div>
                    <div className={styles.summaryCard}>
                      <span>Đang giữ:</span>
                      <strong>3</strong>
                    </div>
                    <div className={styles.summaryCard}>
                      <span>Win rate:</span>
                      <strong className={styles.winRate}>100%</strong>
                    </div>
                    <div className={styles.summaryCard}>
                      <span>Avg P/L:</span>
                      <strong className={styles.avgProfit}>+3.55%</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'risk' && riskAnalysis && (
              <div className={styles.section}>
                <div className={styles.riskHeader}>
                  <h2 className={styles.sectionTitle}>🛡️ AI Risk Shield</h2>
                  <div className={styles.fearMeter}>
                    <span>Fear Index</span>
                    <div className={styles.fearBar}>
                      <div 
                        className={styles.fearFill} 
                        style={{width: `${riskAnalysis.fearIndex}%`}}
                      ></div>
                    </div>
                    <span className={styles.fearValue}>{riskAnalysis.fearIndex}/100</span>
                  </div>
                </div>

                {riskAnalysis.stopTradingMode && (
                  <div className={styles.alertDanger}>
                    <div className={styles.alertIcon}>🚨</div>
                    <div>
                      <h3>STOP TRADING MODE ACTIVATED</h3>
                      <p>Tâm lý thị trường: <strong>{riskAnalysis.marketSentiment}</strong></p>
                    </div>
                  </div>
                )}

                <div className={styles.alertsGrid}>
                  {riskAnalysis.alerts.map((alert, idx) => (
                    <div 
                      key={idx} 
                      className={alert.type === 'danger' ? styles.alertDanger : styles.alertWarning}
                    >
                      <h4>{alert.title}</h4>
                      <p>{alert.message}</p>
                    </div>
                  ))}
                </div>

                <div className={styles.card}>
                  <h3>📊 Phân tích thị trường</h3>
                  <p className={styles.explanation}>{riskAnalysis.explanation}</p>
                </div>

                <div className={styles.card}>
                  <h3>💡 Khuyến nghị</h3>
                  <ul className={styles.recommendationsList}>
                    {riskAnalysis.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {activeTab === 'discipline' && disciplineAnalysis && (
              <div className={styles.section}>
                <h2 className={styles.sectionTitle}>🧠 AI Discipline Coach</h2>

                <div className={styles.portfolioSection}>
                  <h3>📊 Danh mục của bạn</h3>
                  <p className={styles.portfolioHint}>
                    Quý vị thêm danh mục của quý vị vào đây để AI tư vấn quản trị cảm xúc.
                  </p>
                  <div className={styles.portfolioTable}>
                    <div className={styles.portfolioHeader}>
                      <span>Mã</span>
                      <span>Số lượng CP</span>
                      <span>Giá mua</span>
                      <span>Thành tiền</span>
                    </div>
                    <div className={styles.portfolioInput}>
                      <input type="text" placeholder="VNM" className={styles.portfolioField} />
                      <input type="number" placeholder="1000" className={styles.portfolioField} />
                      <input type="number" placeholder="85,000" className={styles.portfolioField} />
                      <input type="text" readOnly value="85,000,000" className={styles.portfolioFieldReadonly} />
                    </div>
                    <button className={styles.addPortfolioBtn}>+ Thêm cổ phiếu</button>
                  </div>
                </div>

                <div className={styles.chatBox}>
                  <input
                    type="text"
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && askDisciplineCoach()}
                    placeholder="Hỏi AI Coach: 'Tôi có nên mua HPG không?', 'Tôi sợ quá'..."
                    className={styles.chatInput}
                  />
                  <button onClick={askDisciplineCoach} className={styles.chatButton}>
                    Hỏi Coach
                  </button>
                </div>

                {disciplineAnalysis.intervention && (
                  <div className={styles.alertWarning}>
                    <div className={styles.alertIcon}>⚠️</div>
                    <div>
                      <h4>Can thiệp: Cảnh báo hành vi</h4>
                      <p>{disciplineAnalysis.message}</p>
                    </div>
                  </div>
                )}

                {!disciplineAnalysis.intervention && (
                  <div className={styles.card}>
                    <h4>Phản hồi từ AI Coach</h4>
                    <p>{disciplineAnalysis.message}</p>
                  </div>
                )}

                {disciplineAnalysis.behaviorInsights && (
                  <div className={styles.behaviorGrid}>
                    <div className={styles.behaviorCard}>
                      <div className={styles.behaviorValue}>
                        {disciplineAnalysis.behaviorInsights.chasedBuys}
                      </div>
                      <div className={styles.behaviorLabel}>Mua đuổi (30 ngày)</div>
                    </div>
                    <div className={styles.behaviorCard}>
                      <div className={styles.behaviorValue}>
                        {disciplineAnalysis.behaviorInsights.panicSells}
                      </div>
                      <div className={styles.behaviorLabel}>Bán hoảng loạn</div>
                    </div>
                    <div className={styles.behaviorCard}>
                      <div className={styles.behaviorValue}>
                        {disciplineAnalysis.behaviorInsights.disciplineScore}
                      </div>
                      <div className={styles.behaviorLabel}>Điểm kỷ luật</div>
                    </div>
                  </div>
                )}

                <div className={styles.card}>
                  <h3>💡 Lời khuyên cá nhân hóa</h3>
                  <ul className={styles.adviceList}>
                    {disciplineAnalysis.advice.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      <footer className={styles.footer}>
        <p>AI Advisor | Powered by Google Gemini 2.0 Flash + VNStock (FREE Real Data) | Beta Version ✨</p>
        <p style={{fontSize: '11px', color: '#94a3b8', marginTop: '4px'}}>
          * Dữ liệu thị trường từ VNStock library - Cập nhật trong ngày | Làm mới để xem giá mới nhất
        </p>
      </footer>
    </div>
  );
}
