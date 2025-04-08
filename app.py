import streamlit as st
import os
import json
import glob
import re

# ----------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------
def load_json(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading JSON file {filepath}: {e}")
        return None

def display_sample(json_path, wav_path):
    sample_data = load_json(json_path)
    if sample_data:
        st.json(sample_data)
    else:
        st.error("Could not load JSON data.")
    if os.path.exists(wav_path):
        with open(wav_path, "rb") as f:
            st.audio(f.read(), format="audio/wav")
    else:
        st.error(f"WAV file not found: {wav_path}")

def group_by_attempt(json_files, pattern):
    """
    Groups the json_files by attempt number.
    The regex pattern should capture the attempt number as group 2.
    Returns a dict: {attempt_number: [filepath, ...]}.
    """
    groups = {}
    regex = re.compile(pattern)
    for filepath in json_files:
        filename = os.path.basename(filepath)
        match = regex.match(filename)
        if match:
            # match.group(2) contains the attempt number
            attempt = match.group(2)
            groups.setdefault(attempt, []).append(filepath)
    return groups

def display_grouped_samples(folder, title, regex_pattern):
    st.header(title)
    json_files = sorted(glob.glob(os.path.join(folder, "*.json")))
    if not json_files:
        st.info(f"No JSON files found in the '{folder}' folder.")
        return

    groups = group_by_attempt(json_files, regex_pattern)
    # Iterate over attempts sorted as integers
    for attempt in sorted(groups.keys(), key=lambda x: int(x)):
        st.subheader(f"Attempt {attempt}")
        group_files = groups[attempt]

        # Use the first file's JSON to optionally get a prompt description.
        first_json = load_json(group_files[0])
        if first_json and "input_text" in first_json:
            st.markdown(f"**Prompt:** {first_json['input_text']}")
        else:
            st.markdown("**Prompt:** (no description available)")

        for json_file in group_files:
            filename = os.path.basename(json_file)
            # Extract the voice name from the filename (assumes format: voice-attempt-*)
            voice_match = re.match(r"^(.*?)-attempt-", filename)
            voice = voice_match.group(1) if voice_match else "unknown"
            # Construct the corresponding WAV file path.
            wav_file = os.path.join(folder, os.path.splitext(filename)[0] + ".wav")
            st.markdown(f"**Voice:** {voice}")
            display_sample(json_file, wav_file)
            st.markdown("---")
        st.markdown("###")

# ----------------------------------------------------------------
# Main page setup
# ----------------------------------------------------------------
st.title("Kokoro TTS Testing Results")
st.write(
    """
All tests use 16-bit, 24 kHz audio, which is the default for the Kokoro [TTS model](https://huggingface.co/hexgrad/Kokoro-82M).
This model supports a variety of languages and voices and is available with an [online demo](https://huggingface.co/spaces/hexgrad/Kokoro-TTS).
"""
)

st.write(
    """
Kokoro is a lightweight TTS model with just 82 million parameters. Despite its compact size, it delivers surprisingly high audio quality and excels in generation speed, 
making it a strong candidate for real-time applications.
"""
)

st.subheader("TL;DR")
st.write(
    """
Kokoro can confidently be used as a TTS provider for Mandrake thanks to its efficiency: it consumes around **1.3 GB of VRAM per request**, allowing it to handle **~35 simultaneous requests** 
on an average 48 GB NVIDIA A6000 GPU. This makes it both **fast** and **resource-friendly**, ideal for scaling voice services.
"""
)

# ----------------------------------------------------------------
# Section: Samples (grouped by attempt)
# ----------------------------------------------------------------
display_grouped_samples("samples", "Samples", r"^(.*?)-attempt-(\d+)\.json$")

# ----------------------------------------------------------------
# Conclusion
# ----------------------------------------------------------------

st.header("Conclusion")
st.markdown(
    """
Based on these tests, the Kokoro TTS model exhibits impressive performance in generating high-quality speech audio rapidly, while also underscoring important resource considerations.

### Generation Speed Factor
For each synthesis run, two core metrics are recorded:
- **total_generation_time_sec:** The time (in seconds) it takes to generate the audio.
- **audio_duration_sec:** The duration (in seconds) of the generated audio.

The **Speed Factor**, which indicates how many seconds of audio are produced per second of generation time, is calculated using the formula:
""")

st.latex(r"""
\text{Speed Factor} = \frac{\text{Audio Duration (sec)}}{\text{Total Generation Time (sec)}}
""")

st.markdown(
    """
For instance, one sample using voice `af_alloy` in Attempt 1 showed a speed factor of approximately **32.7×**. Across all samples, the speed factor varies from about 12× to as high as 53×, with an overall average in the **40–45× range**.

### Latency Calculations
The system records the time taken to produce the first audio chunk, referred to as **first_chunk_latency_sec**. When aggregated over all samples, the average first chunk latency comes out to be approximately **0.2009 seconds**. This low latency ensures a rapid initial response, which is key for a seamless user experience.

### Resource Utilization and Audio Quality
- **GPU Memory::**  
  A single TTS request utilizes approximately 1.3 GB of GPU memory. For example, one NVIDIA A6000 GPU (48 GB of VRAM) can handle up to ~35 simultaneous requests, making this solution lightweight, efficient, and scalable—ideal even for production environments.

- **Audio Format:**  
  The model supports only 24 kHz, 16-bit audio.

### Summary
While the cumulative audio duration in testing reached up to 1 minute and 52 seconds, the Kokoro TTS model proved to be extremely efficient, generating audio 30× to 50× faster than real time with a low average latency of just 0.2009 seconds.

Each request consumes approximately 1.3 GB of GPU memory, which is actually quite reasonable—allowing a high-end GPU like the NVIDIA A6000 to handle up to 35 concurrent requests. This makes the model not only fast and high-quality but also surprisingly scalable.

Overall, Kokoro delivers rapid, high-quality speech synthesis with excellent responsiveness, all while maintaining a balanced and efficient use of GPU resources—making it a strong choice for real-world TTS applications.
    """
)
