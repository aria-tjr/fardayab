"""
Database models using SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List, Dict
import logging

from ..config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()

class Signal(Base):
    """Signal model for storing trading signals"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # LONG or SHORT
    signal_type = Column(String(20), nullable=False)  # trend_following or mean_reversion
    timeframe = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)
    rationale = Column(JSON, nullable=True)  # Store rationale as JSON
    conditions_met = Column(JSON, nullable=True)  # Store conditions as JSON
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    result = Column(String(20), nullable=True)  # WIN, LOSS, or None
    pnl = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    chart_image = Column(Text, nullable=True)  # Base64 encoded chart
    
    def __repr__(self):
        return f"<Signal(symbol={self.symbol}, direction={self.direction}, confidence={self.confidence})>"

class Content(Base):
    """Content model for storing generated content"""
    __tablename__ = 'content'
    
    id = Column(Integer, primary_key=True)
    content_type = Column(String(50), nullable=False)  # market_summary, education, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default='fa')
    tone = Column(String(20), default='professional')
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=False)
    published_timestamp = Column(DateTime, nullable=True)
    telegram_message_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Content(type={self.content_type}, title={self.title})>"

class MarketData(Base):
    """Market data model for storing historical data"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, timeframe={self.timeframe}, timestamp={self.timestamp})>"

class Performance(Base):
    """Performance tracking model"""
    __tablename__ = 'performance'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    total_signals = Column(Integer, default=0)
    winning_signals = Column(Integer, default=0)
    losing_signals = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<Performance(date={self.date}, win_rate={self.win_rate})>"

class DatabaseManager:
    """Database manager for handling all database operations"""
    
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_signal(self, signal_data: Dict) -> Optional[Signal]:
        """Save a trading signal to database with proper data mapping"""
        try:
            session = self.get_session()
            
            # Map signal data to database fields
            db_signal_data = {
                'symbol': signal_data.get('symbol'),
                'direction': signal_data.get('direction'),
                'signal_type': signal_data.get('type', 'unknown'),
                'timeframe': signal_data.get('timeframe', '5m'),
                'entry_price': signal_data.get('entry_price'),
                'stop_loss': signal_data.get('stop_loss'),
                'take_profit': signal_data.get('take_profit'),
                'risk_reward': signal_data.get('risk_reward'),
                'confidence': signal_data.get('confidence'),
                'volume_24h': signal_data.get('volume_24h'),
                'price_change_24h': signal_data.get('price_change_24h'),
                'rationale': signal_data.get('rationale'),
                'conditions_met': signal_data.get('conditions_met'),
                'timestamp': signal_data.get('timestamp', datetime.utcnow()),
                'chart_image': signal_data.get('chart_image')
            }
            
            signal = Signal(**db_signal_data)
            session.add(signal)
            session.commit()
            session.refresh(signal)
            session.close()
            
            logger.info(f"Signal saved: {signal.symbol} {signal.direction} (ID: {signal.id})")
            return signal
            
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return None
    
    def get_active_signals(self) -> List[Signal]:
        """Get all active signals"""
        try:
            session = self.get_session()
            signals = session.query(Signal).filter(Signal.is_active == True).all()
            session.close()
            return signals
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    def update_signal_result(self, signal_id: int, result: str, pnl: float, exit_price: float):
        """Update signal with result"""
        try:
            session = self.get_session()
            signal = session.query(Signal).filter(Signal.id == signal_id).first()
            if signal:
                signal.result = result
                signal.pnl = pnl
                signal.exit_price = exit_price
                signal.exit_timestamp = datetime.utcnow()
                signal.is_active = False
                session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error updating signal result: {e}")
    
    def save_content(self, content_data: Dict) -> Optional[Content]:
        """Save generated content with proper mapping"""
        try:
            session = self.get_session()
            
            # Map content data to database fields
            db_content_data = {
                'content_type': content_data.get('content_type'),
                'title': content_data.get('title'),
                'content': content_data.get('content'),
                'language': content_data.get('language', 'fa'),
                'tone': content_data.get('tone', 'professional'),
                'timestamp': datetime.utcnow()
            }
            
            content = Content(**db_content_data)
            session.add(content)
            session.commit()
            session.refresh(content)
            session.close()
            
            logger.info(f"Content saved: {content.content_type} - {content.title}")
            return content
            
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            return None
    
    def get_recent_signals(self, limit: int = 10) -> List[Signal]:
        """Get recent signals"""
        try:
            session = self.get_session()
            signals = session.query(Signal).order_by(Signal.timestamp.desc()).limit(limit).all()
            session.close()
            return signals
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    def get_signals_by_symbol(self, symbol: str, limit: int = 50) -> List[Signal]:
        """Get signals for a specific symbol"""
        try:
            session = self.get_session()
            signals = session.query(Signal).filter(
                Signal.symbol == symbol
            ).order_by(Signal.timestamp.desc()).limit(limit).all()
            session.close()
            return signals
        except Exception as e:
            logger.error(f"Error getting signals by symbol: {e}")
            return []
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Get performance statistics (focused on Win Rate and signal count per spec)"""
        try:
            session = self.get_session()
            
            # Get signals from last N days
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all signals (including pending ones for total count)
            all_signals = session.query(Signal).filter(
                Signal.timestamp >= start_date
            ).all()
            
            # Get only completed signals for win rate calculation
            completed_signals = session.query(Signal).filter(
                Signal.timestamp >= start_date,
                Signal.result.isnot(None)
            ).all()
            
            if not all_signals:
                return {
                    'total_signals': 0,
                    'winning_signals': 0,
                    'losing_signals': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0,
                    'signals_per_day': 0.0,
                    'pending_signals': 0
                }
            
            total_signals = len(all_signals)
            pending_signals = len([s for s in all_signals if s.result is None])
            winning_signals = len([s for s in completed_signals if s.result == 'WIN'])
            losing_signals = len([s for s in completed_signals if s.result == 'LOSS'])
            
            # Win rate calculation (per spec: focus on this metric)
            win_rate = (winning_signals / len(completed_signals)) * 100 if completed_signals else 0.0
            
            # Signals per day
            signals_per_day = total_signals / max(days, 1)
            
            total_pnl = sum([s.pnl or 0 for s in completed_signals])
            
            wins = [s.pnl for s in completed_signals if s.result == 'WIN' and s.pnl]
            losses = [s.pnl for s in completed_signals if s.result == 'LOSS' and s.pnl]
            
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            
            profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0
            
            session.close()
            
            return {
                'total_signals': total_signals,
                'winning_signals': winning_signals,
                'losing_signals': losing_signals,
                'pending_signals': pending_signals,
                'win_rate': win_rate,
                'signals_per_day': signals_per_day,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor
            }
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    def save_market_data(self, symbol: str, timeframe: str, df):
        """Save market data to database"""
        try:
            session = self.get_session()
            
            # Convert dataframe to records
            records = []
            for timestamp, row in df.iterrows():
                record = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': timestamp,
                    'open_price': row['open'],
                    'high_price': row['high'],
                    'low_price': row['low'],
                    'close_price': row['close'],
                    'volume': row['volume']
                }
                records.append(record)
            
            # Bulk insert
            session.bulk_insert_mappings(MarketData, records)
            session.commit()
            session.close()
            
            logger.info(f"Market data saved: {symbol} {timeframe}")
            
        except Exception as e:
            logger.error(f"Error saving market data: {e}")
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
