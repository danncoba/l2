from agents.guidance import provide_guidance


async def test_guidance_recurring_with_file():
    response = await provide_guidance()
