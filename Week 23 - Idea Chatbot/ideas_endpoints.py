

# ------------------------------------------------------------------------------
# STEP 7: Ideas List Endpoint (NEW in Lesson 4.1)
# ------------------------------------------------------------------------------
# Retrieve all saved ideas from the database

@app.get("/ideas")
def list_ideas(limit: int = 100, offset: int = 0):
    """
    Get all saved ideas from the database.
    
    Args:
        limit (int): Maximum number of ideas to return (default 100)
        offset (int): Number of ideas to skip for pagination (default 0)
    
    Returns:
        Dict with ideas array and metadata
    
    Example:
        GET /ideas?limit=10&offset=0
    """
    try:
        ideas = get_all_ideas(limit=limit, offset=offset)
        total = get_idea_count()
        
        return {
            "ideas": ideas,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        return {
            "error": f"Failed to retrieve ideas: {str(e)}",
            "ideas": []
        }


@app.get("/ideas/{idea_id}")
def get_idea(idea_id: int):
    """
    Get a single idea by ID.
    
    Args:
        idea_id (int): The idea ID
    
    Returns:
        ExtractedIdea or error
    """
    try:
        idea = get_idea_by_id(idea_id)
        
        if idea:
            return idea
        else:
            return {"error": f"Idea {idea_id} not found"}
    except Exception as e:
        return {"error": f"Failed to retrieve idea: {str(e)}"}
