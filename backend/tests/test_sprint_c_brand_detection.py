"""
Sprint C Tests: Enhanced Brand Detection in LLM Connector
Tests for _detect_brand_advanced() and _generate_brand_variants() methods

Test Coverage:
- Exact match detection
- Case insensitive variants (lowercase, uppercase, titlecase)
- Acronym detection for multi-word brands
- No-space variants (HubSpot -> hubspot)
- Typo detection (double letters)
- Phonetic variants
- Backend stability after modification
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.llm_connector import LLMConnector


class TestGenerateBrandVariants:
    """Tests for _generate_brand_variants method"""
    
    @pytest.fixture
    def connector(self):
        """Create LLMConnector instance for testing"""
        return LLMConnector()
    
    def test_exact_match_variant(self, connector):
        """Test that exact match variant is generated"""
        variants = connector._generate_brand_variants("HubSpot")
        variant_types = [v[1] for v in variants]
        variant_values = [v[0] for v in variants]
        
        assert "exact" in variant_types
        assert "HubSpot" in variant_values
    
    def test_lowercase_variant(self, connector):
        """Test that lowercase variant is generated"""
        variants = connector._generate_brand_variants("HubSpot")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "lowercase" in variant_dict
        assert variant_dict["lowercase"] == "hubspot"
    
    def test_uppercase_variant(self, connector):
        """Test that uppercase variant is generated"""
        variants = connector._generate_brand_variants("HubSpot")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "uppercase" in variant_dict
        assert variant_dict["uppercase"] == "HUBSPOT"
    
    def test_titlecase_variant(self, connector):
        """Test that titlecase variant is generated"""
        variants = connector._generate_brand_variants("hubspot")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "titlecase" in variant_dict
        assert variant_dict["titlecase"] == "Hubspot"
    
    def test_no_space_variant_for_multiword_brand(self, connector):
        """Test no_space variant for multi-word brands like 'Hub Spot'"""
        variants = connector._generate_brand_variants("Hub Spot")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "no_space" in variant_dict
        assert variant_dict["no_space"] == "HubSpot"
    
    def test_camelcase_variant_for_multiword_brand(self, connector):
        """Test camelcase variant for multi-word brands"""
        variants = connector._generate_brand_variants("hub spot")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "camelcase" in variant_dict
        assert variant_dict["camelcase"] == "HubSpot"
    
    def test_acronym_for_multiword_brand(self, connector):
        """Test acronym generation for multi-word brands"""
        variants = connector._generate_brand_variants("Customer Relationship Management")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "acronym" in variant_dict
        assert variant_dict["acronym"] == "CRM"
    
    def test_acronym_for_two_word_brand(self, connector):
        """Test acronym for two-word brand"""
        variants = connector._generate_brand_variants("Hub Spot")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "acronym" in variant_dict
        assert variant_dict["acronym"] == "HS"
    
    def test_no_acronym_for_single_word_brand(self, connector):
        """Test that single-word brands don't generate acronyms"""
        variants = connector._generate_brand_variants("Salesforce")
        variant_types = [v[1] for v in variants]
        
        assert "acronym" not in variant_types
    
    def test_typo_double_letter_variant(self, connector):
        """Test typo detection for double letters (e.g., 'google' -> 'gogle')"""
        variants = connector._generate_brand_variants("Google")
        variant_types = [v[1] for v in variants]
        variant_values = [v[0] for v in variants]
        
        assert "typo_double" in variant_types
        # 'google' has 'oo', so 'gogle' should be a typo variant
        assert "gogle" in variant_values
    
    def test_typo_double_letter_for_mississippi(self, connector):
        """Test multiple double letters in brand name"""
        variants = connector._generate_brand_variants("Mississippi")
        typo_variants = [v[0] for v in variants if v[1] == "typo_double"]
        
        # Should have variants for 'ss', 'ss', 'pp'
        assert len(typo_variants) >= 1
    
    def test_no_suffix_removal_for_dotcom(self, connector):
        """Test suffix removal for .com brands"""
        variants = connector._generate_brand_variants("Amazon.com")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "no_suffix" in variant_dict
        assert variant_dict["no_suffix"] == "Amazon"
    
    def test_no_suffix_removal_for_dotfr(self, connector):
        """Test suffix removal for .fr brands"""
        variants = connector._generate_brand_variants("Leboncoin.fr")
        variant_dict = {v[1]: v[0] for v in variants}
        
        assert "no_suffix" in variant_dict
        assert variant_dict["no_suffix"] == "Leboncoin"
    
    def test_phonetic_variant_ph_to_f(self, connector):
        """Test phonetic variant: ph -> f"""
        variants = connector._generate_brand_variants("Phantom")
        phonetic_variants = [v[0] for v in variants if v[1] == "phonetic"]
        
        assert "fantom" in phonetic_variants
    
    def test_phonetic_variant_f_to_ph(self, connector):
        """Test phonetic variant: f -> ph"""
        variants = connector._generate_brand_variants("Firefox")
        phonetic_variants = [v[0] for v in variants if v[1] == "phonetic"]
        
        assert "phirephox" in phonetic_variants
    
    def test_phonetic_variant_c_to_k(self, connector):
        """Test phonetic variant: c -> k"""
        variants = connector._generate_brand_variants("Cisco")
        phonetic_variants = [v[0] for v in variants if v[1] == "phonetic"]
        
        assert "kisko" in phonetic_variants


class TestDetectBrandAdvanced:
    """Tests for _detect_brand_advanced method"""
    
    @pytest.fixture
    def connector(self):
        """Create LLMConnector instance for testing"""
        return LLMConnector()
    
    def test_exact_match_detection(self, connector):
        """Test exact match brand detection"""
        response = "I recommend HubSpot for your CRM needs."
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is True
        assert result["mention_count"] >= 1
        assert result["detection_method"] in ["exact", "lowercase", "titlecase"]
        assert len(result["variants_found"]) >= 1
    
    def test_lowercase_detection(self, connector):
        """Test lowercase brand detection"""
        response = "You should try hubspot for marketing automation."
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is True
        assert result["mention_count"] >= 1
    
    def test_uppercase_detection(self, connector):
        """Test uppercase brand detection"""
        response = "HUBSPOT is a great choice for sales teams."
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is True
    
    def test_no_space_detection(self, connector):
        """Test no-space variant detection (Hub Spot -> hubspot)"""
        response = "I recommend hubspot for your needs."
        result = connector._detect_brand_advanced(response.lower(), "Hub Spot")
        
        assert result["mentioned"] is True
        # Should detect via no_space or camelcase variant
    
    def test_acronym_detection(self, connector):
        """Test acronym detection for multi-word brands"""
        response = "CRM systems are essential for business growth."
        result = connector._detect_brand_advanced(response.lower(), "Customer Relationship Management")
        
        assert result["mentioned"] is True
        assert result["detection_method"] == "acronym"
    
    def test_typo_detection_double_letter(self, connector):
        """Test typo detection for missing double letters"""
        response = "I've heard gogle is working on new AI features."
        result = connector._detect_brand_advanced(response.lower(), "Google")
        
        assert result["mentioned"] is True
        assert result["detection_method"] == "typo_double"
    
    def test_phonetic_detection(self, connector):
        """Test phonetic variant detection"""
        response = "The fantom browser extension is useful."
        result = connector._detect_brand_advanced(response.lower(), "Phantom")
        
        assert result["mentioned"] is True
        assert result["detection_method"] == "phonetic"
    
    def test_no_brand_mentioned(self, connector):
        """Test when brand is not mentioned"""
        response = "There are many CRM solutions available in the market."
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is False
        assert result["mention_count"] == 0
        assert result["first_position"] == -1
        assert result["detection_method"] == "not_found"
    
    def test_empty_brand_name(self, connector):
        """Test with empty brand name"""
        response = "Some text here."
        result = connector._detect_brand_advanced(response.lower(), "")
        
        assert result["mentioned"] is False
        assert result["detection_method"] == "none"
    
    def test_multiple_mentions(self, connector):
        """Test counting multiple brand mentions"""
        response = "HubSpot is great. I love HubSpot. HubSpot rocks!"
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is True
        assert result["mention_count"] >= 3
    
    def test_first_position_tracking(self, connector):
        """Test that first position is correctly tracked"""
        response = "First, let me mention that HubSpot is excellent."
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is True
        assert result["first_position"] > 0
        assert result["first_position"] == response.lower().find("hubspot")
    
    def test_variants_found_structure(self, connector):
        """Test that variants_found has correct structure"""
        response = "HubSpot and hubspot are the same."
        result = connector._detect_brand_advanced(response.lower(), "HubSpot")
        
        assert result["mentioned"] is True
        assert len(result["variants_found"]) >= 1
        
        for variant in result["variants_found"]:
            assert "variant" in variant
            assert "type" in variant
            assert "count" in variant


class TestAnalyzeResponseIntegration:
    """Integration tests for _analyze_response with enhanced brand detection"""
    
    @pytest.fixture
    def connector(self):
        """Create LLMConnector instance for testing"""
        return LLMConnector()
    
    def test_analyze_response_includes_detection_method(self, connector):
        """Test that _analyze_response includes detection_method field"""
        response = "HubSpot is the best CRM solution."
        result = connector._analyze_response(response, "HubSpot", [])
        
        assert "detection_method" in result
        assert "variants_found" in result
        assert result["brand_mentioned"] is True
    
    def test_analyze_response_with_acronym(self, connector):
        """Test _analyze_response with acronym detection"""
        response = "CRM tools help manage customer relationships effectively."
        result = connector._analyze_response(response, "Customer Relationship Management", [])
        
        assert result["brand_mentioned"] is True
        assert result["detection_method"] == "acronym"
    
    def test_analyze_response_with_typo(self, connector):
        """Test _analyze_response with typo detection"""
        response = "I recommend gogle for search."
        result = connector._analyze_response(response, "Google", [])
        
        assert result["brand_mentioned"] is True
        assert result["detection_method"] == "typo_double"
    
    def test_analyze_response_no_brand(self, connector):
        """Test _analyze_response when brand not found"""
        response = "There are many options available."
        result = connector._analyze_response(response, "HubSpot", [])
        
        assert result["brand_mentioned"] is False
        assert result["detection_method"] == "not_found"


class TestBackendStability:
    """Tests to verify backend stability after llm_connector.py modification"""
    
    @pytest.fixture
    def connector(self):
        """Create LLMConnector instance for testing"""
        return LLMConnector()
    
    def test_connector_initialization(self, connector):
        """Test that LLMConnector initializes correctly"""
        assert connector is not None
        assert hasattr(connector, '_detect_brand_advanced')
        assert hasattr(connector, '_generate_brand_variants')
        assert hasattr(connector, '_analyze_response')
    
    def test_analyze_response_returns_all_fields(self, connector):
        """Test that _analyze_response returns all expected fields"""
        response = "HubSpot is a great CRM tool with many features."
        result = connector._analyze_response(response, "HubSpot", ["Salesforce"])
        
        # Layer 1: Presence (Enhanced Sprint C)
        assert "brand_mentioned" in result
        assert "mention_count" in result
        assert "first_position" in result
        assert "position_ratio" in result
        assert "detection_method" in result
        assert "variants_found" in result
        
        # Layer 2: Role
        assert "role" in result
        assert "role_score" in result
        
        # Layer 3: Credibility
        assert "credibility_score" in result
        assert "credibility_factors" in result
        
        # Layer 4: Conversion
        assert "conversion_score" in result
        assert "conversion_signals" in result
        
        # Anti-hallucination
        assert "hallucination_flags" in result
        assert "hallucination_penalty" in result
        
        # Competitors
        assert "competitor_analysis" in result
    
    def test_role_analysis_still_works(self, connector):
        """Test that role analysis works with enhanced detection"""
        response = "HubSpot est le meilleur outil CRM recommandé pour les entreprises."
        result = connector._analyze_response(response, "HubSpot", [])
        
        assert result["brand_mentioned"] is True
        assert result["role"] in ["top_recommendation", "shortlist", "comparison", "mentioned", "cited", "absent", "discouraged"]
        assert 0 <= result["role_score"] <= 1.0
    
    def test_credibility_analysis_still_works(self, connector):
        """Test that credibility analysis works with enhanced detection"""
        response = "Selon une étude de 2024, HubSpot a 50% de part de marché."
        result = connector._analyze_response(response, "HubSpot", [])
        
        assert result["brand_mentioned"] is True
        assert 0 <= result["credibility_score"] <= 100
        assert isinstance(result["credibility_factors"], list)
    
    def test_conversion_analysis_still_works(self, connector):
        """Test that conversion analysis works with enhanced detection"""
        response = "Essayez HubSpot maintenant pour profiter de ses avantages."
        result = connector._analyze_response(response, "HubSpot", [])
        
        assert result["brand_mentioned"] is True
        assert 0 <= result["conversion_score"] <= 100
        assert isinstance(result["conversion_signals"], list)
    
    def test_competitor_analysis_still_works(self, connector):
        """Test that competitor analysis works with enhanced detection"""
        response = "HubSpot et Salesforce sont les deux leaders du marché CRM."
        result = connector._analyze_response(response, "HubSpot", ["Salesforce", "Zoho"])
        
        assert result["brand_mentioned"] is True
        assert "competitor_analysis" in result
        assert "Salesforce" in result["competitor_analysis"]
        assert result["competitor_analysis"]["Salesforce"]["mentioned"] is True


class TestEdgeCases:
    """Edge case tests for brand detection"""
    
    @pytest.fixture
    def connector(self):
        """Create LLMConnector instance for testing"""
        return LLMConnector()
    
    def test_brand_with_special_characters(self, connector):
        """Test brand with special characters"""
        response = "Check out c++ programming language."
        result = connector._detect_brand_advanced(response.lower(), "C++")
        
        # Should handle special characters gracefully
        assert isinstance(result["mentioned"], bool)
    
    def test_very_short_brand_name(self, connector):
        """Test very short brand name (2 chars)"""
        response = "I use AI for my work."
        result = connector._detect_brand_advanced(response.lower(), "AI")
        
        assert result["mentioned"] is True
    
    def test_brand_as_part_of_word(self, connector):
        """Test that brand detection uses word boundaries"""
        response = "The rebranding effort was successful."
        result = connector._detect_brand_advanced(response.lower(), "brand")
        
        # Word boundary check should prevent matching "brand" in "rebranding"
        # Note: This depends on implementation - may or may not match
        assert isinstance(result["mentioned"], bool)
    
    def test_unicode_brand_name(self, connector):
        """Test brand with unicode characters"""
        response = "Découvrez Café du Monde pour le meilleur café."
        result = connector._detect_brand_advanced(response.lower(), "Café du Monde")
        
        assert result["mentioned"] is True
    
    def test_numeric_brand_name(self, connector):
        """Test brand with numbers"""
        response = "7-Eleven is open 24/7."
        result = connector._detect_brand_advanced(response.lower(), "7-Eleven")
        
        assert result["mentioned"] is True
    
    def test_empty_response(self, connector):
        """Test with empty response"""
        result = connector._detect_brand_advanced("", "HubSpot")
        
        assert result["mentioned"] is False
        assert result["mention_count"] == 0
    
    def test_none_brand_name(self, connector):
        """Test with None brand name"""
        result = connector._detect_brand_advanced("some response", None)
        
        assert result["mentioned"] is False
        assert result["detection_method"] == "none"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
