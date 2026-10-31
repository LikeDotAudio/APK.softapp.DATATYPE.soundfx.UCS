// Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
// MIT Licence. Full text in LICENSE at the root.
//! Announce where the bundle's data lives. With `links = "apk_ucs"`, cargo exposes this
//! to each direct dependent's build script as DEP_APK_UCS_DIR.
fn main() {
    let dir = std::env::var("CARGO_MANIFEST_DIR").expect("cargo sets CARGO_MANIFEST_DIR");
    println!("cargo:dir={dir}");
    println!("cargo:rerun-if-changed=categories");
    println!("cargo:rerun-if-changed=producer_synonyms.json");
}
