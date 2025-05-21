import unittest
from datetime import datetime
from data_normalizer import DataNormalizer

class TestDataNormalizer(unittest.TestCase):
    """Tests pour la classe DataNormalizer."""
    
    def setUp(self):
        """Initialise les tests."""
        self.normalizer = DataNormalizer()
        
        # Article exemple avec tous les champs
        self.complete_article = {
            "title": "<h1>Test Title</h1>",
            "url": "https://example.com/article",
            "source": "Test Source",
            "scraped_at": "2023-04-10T12:00:00",
            "date": "2023-04-10T10:00:00+00:00",
            "author": "John Doe",
            "summary": "<p>Test summary with <b>HTML</b> tags</p>",
            "content": "<div>Test content with <i>formatting</i></div>",
            "categories": ["AI", "ML", "AI"],  # Doublon intentionnel
            "image_url": "https://example.com/image.jpg"
        }
        
        # Article exemple avec champs manquants
        self.incomplete_article = {
            "title": "Test Title",
            "url": "https://example.com/article"
        }
        
        # Article exemple avec données invalides
        self.invalid_article = {
            "title": "Test Title",
            "url": "invalid-url",
            "source": "Test Source",
            "scraped_at": "2023-04-10T12:00:00",
            "date": "invalid-date",
            "categories": "Single Category"  # String au lieu de liste
        }
    
    def test_normalize_complete_article(self):
        """Test la normalisation d'un article complet."""
        normalized = self.normalizer.normalize_article(self.complete_article)
        
        # Vérification des champs requis
        self.assertEqual(normalized["title"], "Test Title")
        self.assertEqual(normalized["url"], "https://example.com/article")
        self.assertEqual(normalized["source"], "Test Source")
        self.assertEqual(normalized["scraped_at"], "2023-04-10T12:00:00")
        
        # Vérification des champs optionnels
        self.assertEqual(normalized["date"], "2023-04-10T10:00:00+00:00")
        self.assertEqual(normalized["author"], "John Doe")
        self.assertEqual(normalized["summary"], "Test summary with HTML tags")
        self.assertEqual(normalized["content"], "Test content with formatting")
        self.assertEqual(set(normalized["categories"]), {"AI", "ML"})  # Doublons supprimés
        self.assertEqual(normalized["image_url"], "https://example.com/image.jpg")
    
    def test_normalize_incomplete_article(self):
        """Test la normalisation d'un article avec champs manquants."""
        normalized = self.normalizer.normalize_article(self.incomplete_article)
        
        # Vérification des champs requis
        self.assertEqual(normalized["title"], "Test Title")
        self.assertEqual(normalized["url"], "https://example.com/article")
        self.assertEqual(normalized["source"], "")  # Valeur par défaut
        self.assertIn("scraped_at", normalized)  # Date actuelle ajoutée
        
        # Vérification des champs optionnels absents
        self.assertNotIn("date", normalized)
        self.assertNotIn("author", normalized)
        self.assertNotIn("summary", normalized)
        self.assertNotIn("content", normalized)
        self.assertNotIn("categories", normalized)
        self.assertNotIn("image_url", normalized)
    
    def test_normalize_invalid_article(self):
        """Test la normalisation d'un article avec données invalides."""
        normalized = self.normalizer.normalize_article(self.invalid_article)
        
        # Vérification des champs invalides
        self.assertEqual(normalized["url"], "")  # URL invalide
        self.assertIsNone(normalized["date"])  # Date invalide
        self.assertEqual(normalized["categories"], ["Single Category"])  # String converti en liste
    
    def test_normalize_text(self):
        """Test la normalisation de texte."""
        html_text = "<p>Test <b>text</b> with <i>HTML</i> tags</p>"
        normalized = self.normalizer._normalize_text(html_text)
        self.assertEqual(normalized, "Test text with HTML tags")
    
    def test_normalize_url(self):
        """Test la normalisation d'URLs."""
        valid_url = "https://example.com/article"
        invalid_url = "not-a-url"
        
        self.assertEqual(self.normalizer._normalize_url(valid_url), valid_url)
        self.assertEqual(self.normalizer._normalize_url(invalid_url), "")
    
    def test_normalize_date(self):
        """Test la normalisation de dates."""
        # Test différents formats de date
        date_formats = [
            ("2023-04-10T10:00:00+00:00", "2023-04-10T10:00:00+00:00"),  # ISO avec timezone
            ("2023-04-10 10:00:00", "2023-04-10T10:00:00"),  # Format standard
            ("2023-04-10", "2023-04-10T00:00:00"),  # Date simple
            ("invalid-date", None)  # Date invalide
        ]
        
        for input_date, expected in date_formats:
            normalized = self.normalizer._normalize_date(input_date)
            self.assertEqual(normalized, expected)
    
    def test_normalize_categories(self):
        """Test la normalisation de catégories."""
        # Test différents formats de catégories
        category_tests = [
            (["AI", "ML", "AI"], ["AI", "ML"]),  # Liste avec doublons
            ("Single Category", ["Single Category"]),  # String simple
            ([], []),  # Liste vide
            (None, [])  # None
        ]
        
        for input_categories, expected in category_tests:
            normalized = self.normalizer._normalize_categories(input_categories)
            self.assertEqual(set(normalized), set(expected))
    
    def test_normalize_batch(self):
        """Test la normalisation d'un lot d'articles."""
        articles = [self.complete_article, self.incomplete_article, self.invalid_article]
        normalized_batch = self.normalizer.normalize_batch(articles)
        
        self.assertEqual(len(normalized_batch), 3)  # Tous les articles sont conservés
        self.assertTrue(all(isinstance(article, dict) for article in normalized_batch))

if __name__ == "__main__":
    unittest.main() 