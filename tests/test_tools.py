import pytest
from unittest.mock import patch, MagicMock
from tools import search_listings, suggest_outfit, create_fit_card

# ── Test Tool 1 Failure Mode ─────────────────────────────────────────────────

@patch("tools.load_listings")
def test_search_listings_failure_mode(mock_load):
    """Test that search_listings returns an empty list when no items match."""
    # Setup mock data containing one item
    mock_load.return_value = [
        {
            "id": "1", 
            "title": "Vintage Tee", 
            "price": 25.0, 
            "size": "M", 
            "description": "Graphic t-shirt", 
            "category": "tops", 
            "style_tags": []
        }
    ]
    
    # Condition 1: Exceeds max_price
    results_price = search_listings("Vintage Tee", size="M", max_price=5.0)
    assert results_price == [], "Expected empty list when max_price is too low"
    
    # Condition 2: Size doesn't match
    results_size = search_listings("Vintage Tee", size="XL", max_price=30.0)
    assert results_size == [], "Expected empty list when size does not match"
    
    # Condition 3: No keyword matches
    results_keywords = search_listings("Designer Ballgown", size=None, max_price=None)
    assert results_keywords == [], "Expected empty list when no keywords match"


# ── Test Tool 2 Failure Mode ─────────────────────────────────────────────────

@patch("tools._get_groq_client")
def test_suggest_outfit_empty_wardrobe(mock_get_client):
    """Test that an empty wardrobe does not crash and alters the LLM prompt."""
    # Setup mock Groq client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="General styling advice."))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    new_item = {"title": "Cool Hat", "category": "accessories"}
    empty_wardrobe = {"items": []}
    
    # Execute the function
    result = suggest_outfit(new_item, empty_wardrobe)
    
    # Verify it returned the string successfully without crashing
    assert result == "General styling advice."
    
    # Verify the prompt switched to the "empty wardrobe" logic
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    prompt_sent = call_kwargs["messages"][0]["content"]
    assert "empty" in prompt_sent.lower()
    assert "general styling ideas" in prompt_sent.lower()


# ── Test Tool 3 Failure Mode ─────────────────────────────────────────────────

def test_create_fit_card_failure_mode():
    """Test that create_fit_card catches empty outfit strings and returns an error."""
    new_item = {"title": "Cool Hat", "price": 10, "platform": "depop"}
    
    # Test completely empty string
    result_empty = create_fit_card("", new_item)
    assert "Error:" in result_empty
    
    # Test whitespace-only string
    result_space = create_fit_card("   ", new_item)
    assert "Error:" in result_space
    
    # Test None type
    result_none = create_fit_card(None, new_item)
    assert "Error:" in result_none