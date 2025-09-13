from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class AdvancedPersianProcessor:
    """Advanced Persian language processing and content optimization"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
        # Persian language patterns
        self.persian_chars = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
        self.persian_numbers = set('۰۱۲۳۴۵۶۷۸۹')
        self.persian_punctuation = set('،؛؟!')
        
        # Content quality patterns
        self.quality_indicators = {
            'positive': ['عالی', 'خوب', 'مثبت', 'بهتر', 'موفق', 'پیشرفت', 'رشد', 'امیدوار', 'عالی', 'برجسته'],
            'negative': ['بد', 'منفی', 'مشکل', 'کاهش', 'نگران', 'خطر', 'ریسک', 'افت', 'ضعیف', 'نامناسب'],
            'neutral': ['تحلیل', 'بررسی', 'مطالعه', 'گزارش', 'اطلاعات', 'داده', 'آمار', 'نتایج']
        }
        
        # Persian text normalization patterns
        self.normalization_patterns = [
            (r' +', ' '),  # Multiple spaces to single space
            (r'\n+', '\n'),  # Multiple newlines to single newline
            (r'،+', '،'),  # Multiple commas to single comma
            (r'؛+', '؛'),  # Multiple semicolons to single semicolon
            (r'؟+', '؟'),  # Multiple question marks to single
            (r'!+', '!'),  # Multiple exclamation marks to single
        ]
    
    async def process_persian_text(self, text: str) -> Dict[str, Any]:
        """Comprehensive Persian text processing and analysis"""
        try:
            analysis = {
                'original_text': text,
                'normalized_text': self.normalize_persian_text(text),
                'language_analysis': self._analyze_language_characteristics(text),
                'content_quality': self._analyze_content_quality(text),
                'readability_score': self._calculate_readability_score(text),
                'sentiment_analysis': self._analyze_sentiment(text),
                'topic_extraction': self._extract_topics(text),
                'optimization_suggestions': self._get_optimization_suggestions(text)
            }
            
            return analysis
            
        except Exception as e:
            log.error(f"Persian text processing failed: {e}")
            return {'error': str(e)}
    
    def normalize_persian_text(self, text: str) -> str:
        """Normalize Persian text for better processing"""
        try:
            # Apply normalization patterns
            normalized = text
            for pattern, replacement in self.normalization_patterns:
                normalized = re.sub(pattern, replacement, normalized)
            
            # Fix common Persian text issues
            normalized = self._fix_persian_text_issues(normalized)
            
            # Ensure proper spacing around punctuation
            normalized = self._fix_punctuation_spacing(normalized)
            
            return normalized.strip()
            
        except Exception as e:
            log.error(f"Text normalization failed: {e}")
            return text
    
    def _fix_persian_text_issues(self, text: str) -> str:
        """Fix common Persian text issues"""
        fixes = [
            ('ي', 'ی'),  # Arabic yeh to Persian yeh
            ('ك', 'ک'),  # Arabic kaf to Persian kaf
            ('ة', 'ه'),  # Arabic teh marbuta to Persian heh
            ('أ', 'ا'),  # Arabic alef with hamza to Persian alef
            ('إ', 'ا'),  # Arabic alef with hamza below to Persian alef
            ('آ', 'ا'),  # Arabic alef with madda to Persian alef
        ]
        
        for old, new in fixes:
            text = text.replace(old, new)
        
        return text
    
    def _fix_punctuation_spacing(self, text: str) -> str:
        """Fix spacing around Persian punctuation"""
        # Add space before punctuation if missing
        text = re.sub(r'([^\s])([،؛؟!])', r'\1 \2', text)
        
        # Remove extra spaces after punctuation
        text = re.sub(r'([،؛؟!])\s+', r'\1 ', text)
        
        return text
    
    def _analyze_language_characteristics(self, text: str) -> Dict[str, Any]:
        """Analyze Persian language characteristics"""
        try:
            chars = set(text)
            persian_chars = chars.intersection(self.persian_chars)
            persian_numbers = chars.intersection(self.persian_numbers)
            persian_punctuation = chars.intersection(self.persian_punctuation)
            
            return {
                'persian_ratio': len(persian_chars) / len(chars) if chars else 0,
                'persian_char_count': len(persian_chars),
                'persian_number_count': len(persian_numbers),
                'persian_punctuation_count': len(persian_punctuation),
                'total_chars': len(chars),
                'word_count': len(text.split()),
                'sentence_count': len([s for s in text.split('.') if s.strip()]),
                'is_primarily_persian': len(persian_chars) / len(chars) > 0.3 if chars else False
            }
            
        except Exception as e:
            log.error(f"Language analysis failed: {e}")
            return {}
    
    def _analyze_content_quality(self, text: str) -> Dict[str, Any]:
        """Analyze content quality indicators"""
        try:
            text_lower = text.lower()
            
            quality_scores = {}
            for category, words in self.quality_indicators.items():
                count = sum(1 for word in words if word in text_lower)
                quality_scores[category] = count
            
            # Calculate overall quality score
            total_indicators = sum(quality_scores.values())
            if total_indicators > 0:
                positive_ratio = quality_scores['positive'] / total_indicators
                negative_ratio = quality_scores['negative'] / total_indicators
                neutral_ratio = quality_scores['neutral'] / total_indicators
            else:
                positive_ratio = negative_ratio = neutral_ratio = 0
            
            return {
                'quality_scores': quality_scores,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'overall_quality': positive_ratio - negative_ratio + neutral_ratio * 0.5
            }
            
        except Exception as e:
            log.error(f"Content quality analysis failed: {e}")
            return {}
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score for Persian text"""
        try:
            words = text.split()
            sentences = [s for s in text.split('.') if s.strip()]
            
            if not words or not sentences:
                return 0.0
            
            # Basic readability metrics
            avg_words_per_sentence = len(words) / len(sentences)
            avg_chars_per_word = sum(len(word) for word in words) / len(words)
            
            # Persian-specific readability adjustments
            persian_ratio = self._analyze_language_characteristics(text).get('persian_ratio', 0)
            
            # Calculate readability score (0-10, higher is better)
            readability = 10.0
            
            # Penalize very long sentences
            if avg_words_per_sentence > 20:
                readability -= 2
            elif avg_words_per_sentence > 15:
                readability -= 1
            
            # Penalize very long words
            if avg_chars_per_word > 8:
                readability -= 2
            elif avg_chars_per_word > 6:
                readability -= 1
            
            # Bonus for good Persian ratio
            if persian_ratio > 0.8:
                readability += 1
            elif persian_ratio < 0.5:
                readability -= 1
            
            return max(0.0, min(10.0, readability))
            
        except Exception as e:
            log.error(f"Readability calculation failed: {e}")
            return 5.0
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Advanced sentiment analysis for Persian text"""
        try:
            text_lower = text.lower()
            
            # Count sentiment words
            positive_count = sum(1 for word in self.quality_indicators['positive'] if word in text_lower)
            negative_count = sum(1 for word in self.quality_indicators['negative'] if word in text_lower)
            neutral_count = sum(1 for word in self.quality_indicators['neutral'] if word in text_lower)
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            if total_sentiment_words == 0:
                return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            
            # Determine sentiment category
            if sentiment_score > 0.2:
                sentiment = 'positive'
            elif sentiment_score < -0.2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Calculate confidence
            confidence = abs(sentiment_score) * (total_sentiment_words / len(text.split()))
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score,
                'confidence': min(1.0, confidence),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count
            }
            
        except Exception as e:
            log.error(f"Sentiment analysis failed: {e}")
            return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from Persian text"""
        try:
            # Define topic keywords
            topic_keywords = {
                'اقتصاد': ['اقتصاد', 'بازار', 'دلار', 'بیت‌کوین', 'سرمایه', 'سرمایه‌گذاری', 'پول', 'ارز'],
                'ورزش': ['ورزش', 'فوتبال', 'مسابقه', 'تیم', 'بازیکن', 'لیگ', 'قهرمانی', 'ورزشگاه'],
                'تکنولوژی': ['تکنولوژی', 'فناوری', 'هوش مصنوعی', 'دیجیتال', 'نرم‌افزار', 'برنامه', 'اپلیکیشن'],
                'فرهنگ': ['فرهنگ', 'هنر', 'موسیقی', 'فیلم', 'سینما', 'کتاب', 'ادبیات', 'شعر'],
                'سلامت': ['سلامت', 'درمان', 'پزشکی', 'بیماری', 'دارو', 'تغذیه', 'ورزش', 'فیتنس'],
                'سفر': ['سفر', 'گردشگری', 'مقصد', 'هتل', 'رستوران', 'جاذبه', 'توریست', 'مسافرت']
            }
            
            text_lower = text.lower()
            found_topics = []
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    found_topics.append(topic)
            
            return found_topics
            
        except Exception as e:
            log.error(f"Topic extraction failed: {e}")
            return []
    
    def _get_optimization_suggestions(self, text: str) -> List[str]:
        """Get optimization suggestions for Persian text"""
        suggestions = []
        
        try:
            analysis = self._analyze_language_characteristics(text)
            
            # Check Persian ratio
            if analysis.get('persian_ratio', 0) < 0.7:
                suggestions.append("نسبت متن فارسی را افزایش دهید")
            
            # Check readability
            readability = self._calculate_readability_score(text)
            if readability < 6:
                suggestions.append("متن را ساده‌تر و قابل فهم‌تر کنید")
            
            # Check sentence length
            words = text.split()
            sentences = [s for s in text.split('.') if s.strip()]
            if sentences and len(words) / len(sentences) > 20:
                suggestions.append("جملات را کوتاه‌تر کنید")
            
            # Check emoji usage
            emoji_count = sum(1 for char in text if ord(char) > 127 and char not in self.persian_chars)
            if emoji_count < 3:
                suggestions.append("ایموجی‌های بیشتری اضافه کنید")
            
            # Check hashtags
            hashtag_count = text.count('#')
            if hashtag_count < 3:
                suggestions.append("هشتگ‌های مرتبط اضافه کنید")
            elif hashtag_count > 8:
                suggestions.append("تعداد هشتگ‌ها را کاهش دهید")
            
            # Check engagement elements
            if '?' not in text and '!' not in text:
                suggestions.append("عناصر تعاملی (سوال یا تعجب) اضافه کنید")
            
            return suggestions
            
        except Exception as e:
            log.error(f"Optimization suggestions failed: {e}")
            return ["متن را بررسی و بهبود دهید"]
    
    async def enhance_content_for_engagement(self, content: str) -> str:
        """Enhance content for maximum engagement"""
        try:
            # Get analysis
            analysis = await self.process_persian_text(content)
            
            # Apply optimizations
            enhanced = content
            
            # Add engagement hooks if missing
            if '?' not in enhanced and '!' not in enhanced:
                enhanced += '\n\nنظر شما چیست؟ 🤔'
            
            # Ensure proper emoji usage
            emoji_count = sum(1 for char in enhanced if ord(char) > 127 and char not in self.persian_chars)
            if emoji_count < 3:
                enhanced = enhanced.replace('**اقتصاد**', '**📊 اقتصاد**')
                enhanced = enhanced.replace('**ورزش**', '**⚽ ورزش**')
                enhanced = enhanced.replace('**ترند**', '**📱 ترند**')
            
            # Add call-to-action if missing
            if 'نظر' not in enhanced and 'فکر' not in enhanced and 'اشتراک' not in enhanced:
                enhanced += '\n\n💬 نظرات خود را با ما به اشتراک بگذارید!'
            
            # Optimize hashtags
            hashtag_count = enhanced.count('#')
            if hashtag_count < 3:
                suggested_hashtags = ['#فردایاب', '#تحلیل', '#پیش‌بینی']
                enhanced += ' ' + ' '.join(suggested_hashtags)
            elif hashtag_count > 8:
                # Remove excess hashtags
                words = enhanced.split()
                hashtags = [word for word in words if word.startswith('#')]
                non_hashtags = [word for word in words if not word.startswith('#')]
                enhanced = ' '.join(non_hashtags + hashtags[:6])
            
            return enhanced
            
        except Exception as e:
            log.error(f"Content enhancement failed: {e}")
            return content
    
    async def translate_and_optimize(self, text: str, target_language: str = 'fa') -> str:
        """Translate and optimize text for Persian audience"""
        try:
            if target_language == 'fa':
                # If already Persian, just optimize
                return await self.enhance_content_for_engagement(text)
            
            # Translation logic would go here
            # For now, return optimized original text
            return await self.enhance_content_for_engagement(text)
            
        except Exception as e:
            log.error(f"Translation and optimization failed: {e}")
            return text
