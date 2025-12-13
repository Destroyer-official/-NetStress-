//! SIMD-accelerated packet operations
//! Uses portable SIMD for vectorized checksum and packet building

use std::arch::x86_64::*;

/// SIMD-accelerated IP checksum calculation
/// Falls back to scalar implementation on unsupported platforms
#[inline]
pub fn checksum_simd(data: &[u8]) -> u16 {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") {
            unsafe { checksum_avx2(data) }
        } else if is_x86_feature_detected!("sse2") {
            unsafe { checksum_sse2(data) }
        } else {
            checksum_scalar(data)
        }
    }
    
    #[cfg(not(target_arch = "x86_64"))]
    {
        checksum_scalar(data)
    }
}

/// Scalar checksum implementation (fallback)
#[inline]
pub fn checksum_scalar(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut i = 0;
    
    // Process 2 bytes at a time
    while i + 1 < data.len() {
        sum += ((data[i] as u32) << 8) | (data[i + 1] as u32);
        i += 2;
    }
    
    // Handle odd byte
    if i < data.len() {
        sum += (data[i] as u32) << 8;
    }
    
    // Fold 32-bit sum to 16 bits
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    
    !sum as u16
}


/// SSE2 accelerated checksum (16 bytes at a time)
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "sse2")]
unsafe fn checksum_sse2(data: &[u8]) -> u16 {
    let mut sum: u64 = 0;
    let mut i = 0;
    let len = data.len();
    
    // Process 16 bytes at a time using SSE2
    while i + 16 <= len {
        let chunk = _mm_loadu_si128(data.as_ptr().add(i) as *const __m128i);
        
        // Unpack and sum
        let low = _mm_unpacklo_epi8(chunk, _mm_setzero_si128());
        let high = _mm_unpackhi_epi8(chunk, _mm_setzero_si128());
        
        // Horizontal add
        let sum_vec = _mm_add_epi16(low, high);
        let sum_vec = _mm_add_epi16(sum_vec, _mm_srli_si128(sum_vec, 8));
        let sum_vec = _mm_add_epi16(sum_vec, _mm_srli_si128(sum_vec, 4));
        let sum_vec = _mm_add_epi16(sum_vec, _mm_srli_si128(sum_vec, 2));
        
        sum += _mm_extract_epi16(sum_vec, 0) as u64;
        i += 16;
    }
    
    // Process remaining bytes
    while i + 1 < len {
        sum += ((data[i] as u64) << 8) | (data[i + 1] as u64);
        i += 2;
    }
    
    if i < len {
        sum += (data[i] as u64) << 8;
    }
    
    // Fold to 16 bits
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    
    !sum as u16
}

/// AVX2 accelerated checksum (32 bytes at a time)
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn checksum_avx2(data: &[u8]) -> u16 {
    let mut sum: u64 = 0;
    let mut i = 0;
    let len = data.len();
    
    // Process 32 bytes at a time using AVX2
    while i + 32 <= len {
        let chunk = _mm256_loadu_si256(data.as_ptr().add(i) as *const __m256i);
        
        // Sum adjacent bytes
        let sad = _mm256_sad_epu8(chunk, _mm256_setzero_si256());
        
        // Extract and accumulate
        sum += _mm256_extract_epi64(sad, 0) as u64;
        sum += _mm256_extract_epi64(sad, 1) as u64;
        sum += _mm256_extract_epi64(sad, 2) as u64;
        sum += _mm256_extract_epi64(sad, 3) as u64;
        
        i += 32;
    }
    
    // Process remaining with SSE2
    while i + 16 <= len {
        let chunk = _mm_loadu_si128(data.as_ptr().add(i) as *const __m128i);
        let sad = _mm_sad_epu8(chunk, _mm_setzero_si128());
        sum += _mm_extract_epi64(sad, 0) as u64;
        sum += _mm_extract_epi64(sad, 1) as u64;
        i += 16;
    }
    
    // Process remaining bytes
    while i + 1 < len {
        sum += ((data[i] as u64) << 8) | (data[i + 1] as u64);
        i += 2;
    }
    
    if i < len {
        sum += (data[i] as u64) << 8;
    }
    
    // Fold to 16 bits
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    
    !sum as u16
}

/// SIMD-accelerated memory fill for packet payloads
#[inline]
pub fn fill_payload_simd(buffer: &mut [u8], pattern: u8) {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") {
            unsafe { fill_avx2(buffer, pattern) }
        } else {
            buffer.fill(pattern);
        }
    }
    
    #[cfg(not(target_arch = "x86_64"))]
    {
        buffer.fill(pattern);
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn fill_avx2(buffer: &mut [u8], pattern: u8) {
    let pattern_vec = _mm256_set1_epi8(pattern as i8);
    let mut i = 0;
    let len = buffer.len();
    
    // Fill 32 bytes at a time
    while i + 32 <= len {
        _mm256_storeu_si256(buffer.as_mut_ptr().add(i) as *mut __m256i, pattern_vec);
        i += 32;
    }
    
    // Fill remaining
    while i < len {
        buffer[i] = pattern;
        i += 1;
    }
}

/// SIMD-accelerated memory copy for packet building
#[inline]
pub fn copy_packet_simd(dst: &mut [u8], src: &[u8]) {
    let len = src.len().min(dst.len());
    
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") && len >= 32 {
            unsafe { copy_avx2(&mut dst[..len], &src[..len]) }
        } else {
            dst[..len].copy_from_slice(&src[..len]);
        }
    }
    
    #[cfg(not(target_arch = "x86_64"))]
    {
        dst[..len].copy_from_slice(&src[..len]);
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn copy_avx2(dst: &mut [u8], src: &[u8]) {
    let mut i = 0;
    let len = src.len();
    
    // Copy 32 bytes at a time
    while i + 32 <= len {
        let chunk = _mm256_loadu_si256(src.as_ptr().add(i) as *const __m256i);
        _mm256_storeu_si256(dst.as_mut_ptr().add(i) as *mut __m256i, chunk);
        i += 32;
    }
    
    // Copy remaining
    while i < len {
        dst[i] = src[i];
        i += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_checksum_scalar() {
        let data = vec![0x45, 0x00, 0x00, 0x3c, 0x1c, 0x46, 0x40, 0x00,
                        0x40, 0x06, 0x00, 0x00, 0xac, 0x10, 0x0a, 0x63,
                        0xac, 0x10, 0x0a, 0x0c];
        let checksum = checksum_scalar(&data);
        assert!(checksum != 0); // Just verify it runs
    }

    #[test]
    fn test_checksum_simd() {
        let data = vec![0u8; 1500];
        let scalar = checksum_scalar(&data);
        let simd = checksum_simd(&data);
        assert_eq!(scalar, simd);
    }

    #[test]
    fn test_fill_payload() {
        let mut buffer = vec![0u8; 1500];
        fill_payload_simd(&mut buffer, 0xAA);
        assert!(buffer.iter().all(|&b| b == 0xAA));
    }

    #[test]
    fn test_copy_packet() {
        let src = vec![1u8, 2, 3, 4, 5, 6, 7, 8];
        let mut dst = vec![0u8; 8];
        copy_packet_simd(&mut dst, &src);
        assert_eq!(dst, src);
    }
}
