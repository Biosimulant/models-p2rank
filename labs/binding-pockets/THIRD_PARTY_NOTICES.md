# Third-party notices: binding-pockets lab

This is an engineering provenance record produced by `scripts/license_audit.py` (machine-readable detail in `sources/license-audit.json`). It is not legal advice or legal clearance.

## P2Rank 2.5.1 binary distribution

The Java components below are redistributed **unmodified** (apart from the two omissions described next) from the P2Rank 2.5.1 binary distribution (`p2rank_2.5.1.tar.gz`, sha256 `d243f2d9036ac053fefb9407b5fe1c85f4fe077c519fd975ac585e995feab274`), built from https://github.com/rdk/p2rank commit `9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e`. Every jar's sha256 is listed in `sources/license-audit.json` and `sources/jar-inventory.json`. Licenses bundled inside the jars (META-INF/LICENSE*, NOTICE*) remain in place and copies are in `sources/jar-notices/`.

### Components omitted from the shipped runtime

The Lab's runtime archives (`assets/p2rank-runtime-0.zip`, `assets/p2rank-runtime-1.zip`) deliberately omit two jars present in the upstream distribution:

- `bin/lib/vecmath-1.3.1.jar` — its only license text is a 2001 Sun notice restricting use, copying and distribution, and no redistribution grant was found. Every class it contains is also provided by `vecmath-1.5.2.jar` (GPL-2.0 with Classpath Exception), which is shipped.
- `bin/lib/openchart-1.4.2.jar` — LGPL-2.1 charting library for desktop GUI use; its exact corresponding source could not be retained.

With both omitted, P2Rank 2.5.1 produces byte-identical prediction CSVs, residue CSVs and surface-point files on all three reference structures (1CRN, 1STP, 7L13) compared with the unmodified distribution (`reports/runtime-trim-verification.json`). The rows below for these two jars describe the upstream distribution, not shipped files.

### P2Rank license (MIT)

```
MIT License

Copyright (c) 2017-2025 Radoslav Krivák, David Hoksza, Lukáš Jendele, Petr Škoda and other contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Summary

113 jars: permissive 74, strong-copyleft 7, unknown 1, weak-copyleft 31. Unresolved: vecmath-1.3.1.jar.

Strong-copyleft components combined with P2Rank (MIT) in the distributed runtime: `FasterForest-2.5.2.jar` (GPL-2.0), `FastRandomForest_0.99.jar` (GPL-2.0), `FastRandomForest_0.99_src.jar` (GPL-2.0), `jclipboardhelper-0.1.0.jar` (GPL-3.0), `jfilechooser-bookmarks-0.1.6.jar` (GPL-3.0), `vecmath-1.5.2.jar` (GPL-2.0-with-classpath-exception), `weka-dev-3.9.6.jar` (GPL-3.0). Redistributing the runtime carries those licenses' source-availability obligations; see Corresponding source below.

### Open items flagged for review before public redistribution

- `openchart-1.4.2.jar`: LGPL-2.1, **corresponding source not retained**. Not on Maven Central (SHA-1 and a:openchart searches empty). Coordinates from the forester-1.039 POM, which says the JBoss repository is needed for openchart; P2Rank build.gradle also declares that repository. Jar bytes NOT verified against the JBoss copy. License from the LGPL-2.1 text bundled at the jar root.
- `vecmath-1.3.1.jar`: **unresolved** (LicenseRef-Sun-restrictive-notice). FLAG: restrictive/proprietary licensing language found ['vecmath-1.3.1.jar!/javax/vecmath/legal.txt']; no redistribution grant located.

Non-jar files also shipped in `bin/lib/`: `all-1.1.2.pom` (Maven POM of netlib-java `com.github.fommil.netlib:all:1.1.2`, BSD-3-Clause like the netlib jars).

### Jar table

| Jar | Coordinates | License | Class | Source |
|---|---|---|---|---|
| `p2rank.jar` | github:rdk/p2rank@9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e (P2Rank 2.5.1 main jar) | MIT | permissive | https://github.com/rdk/p2rank/tree/9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e |
| `angus-activation-2.0.1.jar` | org.eclipse.angus:angus-activation:2.0.1 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/org/eclipse/angus/angus-activation/2.0.1/angus-activation-2.0.1-sources.jar (if published) |
| `arpack_combined_all-0.1.jar` | net.sourceforge.f2j:arpack_combined_all:0.1 | BSD (variant unspecified) | permissive | https://repo1.maven.org/maven2/net/sourceforge/f2j/arpack_combined_all/0.1/arpack_combined_all-0.1-sources.jar (if published) |
| `beam-core-1.3.8.jar` | uk.ac.ebi.beam:beam-core:1.3.8 | BSD-2-Clause | permissive | https://repo1.maven.org/maven2/uk/ac/ebi/beam/beam-core/1.3.8/beam-core-1.3.8-sources.jar (if published) |
| `beam-func-1.3.8.jar` | uk.ac.ebi.beam:beam-func:1.3.8 | BSD-2-Clause | permissive | https://repo1.maven.org/maven2/uk/ac/ebi/beam/beam-func/1.3.8/beam-func-1.3.8-sources.jar (if published) |
| `biojava-alignment-7.2.2.jar` | org.biojava:biojava-alignment:7.2.2 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/biojava-alignment-7.2.2-sources.jar` |
| `biojava-core-7.2.2.jar` | org.biojava:biojava-core:7.2.2 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/biojava-core-7.2.2-sources.jar` |
| `biojava-structure-7.2.2-rdk.1.jar` | org.biojava:biojava-structure:7.2.2-rdk.1 (fork; P2Rank local-mvn-repo; github:rdk/biojava branch updated-cif-parsing-bug-7.2.2 @ 49c633adae29f9fea58395b4c896e478b677e899) | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/biojava-7.2.2-rdk.1-49c633adae29.tar.gz` |
| `bounce-0.18.jar` | nz.ac.waikato.cms.weka.thirdparty:bounce:0.18 | BSD-3-Clause OR UNKNOWN | permissive | https://repo1.maven.org/maven2/nz/ac/waikato/cms/weka/thirdparty/bounce/0.18/bounce-0.18-sources.jar (if published) |
| `cdk-atomtype-2.11.jar` | org.openscience.cdk:cdk-atomtype:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-atomtype-2.11-sources.jar` |
| `cdk-charges-2.11.jar` | org.openscience.cdk:cdk-charges:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-charges-2.11-sources.jar` |
| `cdk-core-2.11.jar` | org.openscience.cdk:cdk-core:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-core-2.11-sources.jar` |
| `cdk-ctab-2.11.jar` | org.openscience.cdk:cdk-ctab:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-ctab-2.11-sources.jar` |
| `cdk-dict-2.11.jar` | org.openscience.cdk:cdk-dict:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-dict-2.11-sources.jar` |
| `cdk-fingerprint-2.11.jar` | org.openscience.cdk:cdk-fingerprint:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-fingerprint-2.11-sources.jar` |
| `cdk-formula-2.11.jar` | org.openscience.cdk:cdk-formula:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-formula-2.11-sources.jar` |
| `cdk-fragment-2.11.jar` | org.openscience.cdk:cdk-fragment:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-fragment-2.11-sources.jar` |
| `cdk-hash-2.11.jar` | org.openscience.cdk:cdk-hash:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-hash-2.11-sources.jar` |
| `cdk-interfaces-2.11.jar` | org.openscience.cdk:cdk-interfaces:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-interfaces-2.11-sources.jar` |
| `cdk-ioformats-2.11.jar` | org.openscience.cdk:cdk-ioformats:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-ioformats-2.11-sources.jar` |
| `cdk-isomorphism-2.11.jar` | org.openscience.cdk:cdk-isomorphism:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-isomorphism-2.11-sources.jar` |
| `cdk-qsar-2.11.jar` | org.openscience.cdk:cdk-qsar:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-qsar-2.11-sources.jar` |
| `cdk-qsarmolecular-2.11.jar` | org.openscience.cdk:cdk-qsarmolecular:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-qsarmolecular-2.11-sources.jar` |
| `cdk-reaction-2.11.jar` | org.openscience.cdk:cdk-reaction:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-reaction-2.11-sources.jar` |
| `cdk-silent-2.11.jar` | org.openscience.cdk:cdk-silent:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-silent-2.11-sources.jar` |
| `cdk-smarts-2.11.jar` | org.openscience.cdk:cdk-smarts:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-smarts-2.11-sources.jar` |
| `cdk-smiles-2.11.jar` | org.openscience.cdk:cdk-smiles:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-smiles-2.11-sources.jar` |
| `cdk-standard-2.11.jar` | org.openscience.cdk:cdk-standard:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-standard-2.11-sources.jar` |
| `cdk-valencycheck-2.11.jar` | org.openscience.cdk:cdk-valencycheck:2.11 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/cdk-valencycheck-2.11-sources.jar` |
| `ciftools-java-7.0.1.jar` | org.rcsb:ciftools-java:7.0.1 | MIT | permissive | https://repo1.maven.org/maven2/org/rcsb/ciftools-java/7.0.1/ciftools-java-7.0.1-sources.jar (if published) |
| `combinatoricslib3-3.4.0.jar` | com.github.dpaukov:combinatoricslib3:3.4.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/github/dpaukov/combinatoricslib3/3.4.0/combinatoricslib3-3.4.0-sources.jar (if published) |
| `commons-codec-1.19.0.jar` | commons-codec:commons-codec:1.19.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/commons-codec/commons-codec/1.19.0/commons-codec-1.19.0-sources.jar (if published) |
| `commons-compress-1.28.0.jar` | org.apache.commons:commons-compress:1.28.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/commons/commons-compress/1.28.0/commons-compress-1.28.0-sources.jar (if published) |
| `commons-csv-1.14.1.jar` | org.apache.commons:commons-csv:1.14.1 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/commons/commons-csv/1.14.1/commons-csv-1.14.1-sources.jar (if published) |
| `commons-io-2.20.0.jar` | commons-io:commons-io:2.20.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/commons-io/commons-io/2.20.0/commons-io-2.20.0-sources.jar (if published) |
| `commons-lang-2.4.jar` | commons-lang:commons-lang:2.4 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/commons-lang/commons-lang/2.4/commons-lang-2.4-sources.jar (if published) |
| `commons-lang3-3.18.0.jar` | org.apache.commons:commons-lang3:3.18.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/commons/commons-lang3/3.18.0/commons-lang3-3.18.0-sources.jar (if published) |
| `commons-math3-3.6.1.jar` | org.apache.commons:commons-math3:3.6.1 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/commons/commons-math3/3.6.1/commons-math3-3.6.1-sources.jar (if published) |
| `core-1.1.2.jar` | com.github.fommil.netlib:core:1.1.2 | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/core/1.1.2/core-1.1.2-sources.jar (if published) |
| `ejml-core-0.39.jar` | org.ejml:ejml-core:0.39 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/ejml/ejml-core/0.39/ejml-core-0.39-sources.jar (if published) |
| `error_prone_annotations-2.38.0.jar` | com.google.errorprone:error_prone_annotations:2.38.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/errorprone/error_prone_annotations/2.38.0/error_prone_annotations-2.38.0-sources.jar (if published) |
| `euclid-0.22.5.jar` | us.ihmc:euclid:0.22.5 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/us/ihmc/euclid/0.22.5/euclid-0.22.5-sources.jar (if published) |
| `failureaccess-1.0.3.jar` | com.google.guava:failureaccess:1.0.3 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/guava/failureaccess/1.0.3/failureaccess-1.0.3-sources.jar (if published) |
| `faster-molecular-surface-1.0.jar` | cz.cuni.cusbg:faster-molecular-surface:1.0 (P2Rank local-mvn-repo; github:rdk/FasterMolecularSurface@1.0 207cc34debc41f50bab1d879d08da88da9309763) | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/FasterMolecularSurface-1.0-207cc34debc4.tar.gz` |
| `FasterForest-2.5.2.jar` | github:rdk/FasterForest@2.5.2 (246546ac8c184c16dc2f432e8d1d5256776e0b7d) | GPL-2.0 | strong-copyleft | `sources/corresponding-sources/FasterForest-2.5.2-246546ac8c18.tar.gz` |
| `FastRandomForest_0.99.jar` | FastRandomForest 0.99 (Fran Supek; code.google.com/archive/p/fast-random-forest), vendored at rdk/p2rank lib/ | GPL-2.0 | strong-copyleft | `sources/p2rank_2.5.1/bin/lib/FastRandomForest_0.99_src.jar` |
| `FastRandomForest_0.99_src.jar` | FastRandomForest 0.99 source jar, vendored at rdk/p2rank lib/ | GPL-2.0 | strong-copyleft | `sources/p2rank_2.5.1/bin/lib/FastRandomForest_0.99_src.jar` |
| `flatlaf-2.0.jar` | com.formdev:flatlaf:2.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/formdev/flatlaf/2.0/flatlaf-2.0-sources.jar (if published) |
| `forester-1.039.jar` | org.biojava.thirdparty:forester:1.039 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/forester-1.039-sources.jar` |
| `gpars-1.2.1.jar` | org.codehaus.gpars:gpars:1.2.1 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/codehaus/gpars/gpars/1.2.1/gpars-1.2.1-sources.jar (if published) |
| `groovy-4.0.28.jar` | org.apache.groovy:groovy:4.0.28 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/groovy/groovy/4.0.28/groovy-4.0.28-sources.jar (if published) |
| `gson-2.13.1.jar` | com.google.code.gson:gson:2.13.1 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/code/gson/gson/2.13.1/gson-2.13.1-sources.jar (if published) |
| `guava-33.4.8-jre.jar` | com.google.guava:guava:33.4.8-jre | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/guava/guava/33.4.8-jre/guava-33.4.8-jre-sources.jar (if published) |
| `hppc-0.10.0.jar` | com.carrotsearch:hppc:0.10.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/carrotsearch/hppc/0.10.0/hppc-0.10.0-sources.jar (if published) |
| `istack-commons-runtime-4.1.2.jar` | com.sun.istack:istack-commons-runtime:4.1.2 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/com/sun/istack/istack-commons-runtime/4.1.2/istack-commons-runtime-4.1.2-sources.jar (if published) |
| `j2objc-annotations-3.0.0.jar` | com.google.j2objc:j2objc-annotations:3.0.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/j2objc/j2objc-annotations/3.0.0/j2objc-annotations-3.0.0-sources.jar (if published) |
| `jackson-annotations-2.13.4.jar` | com.fasterxml.jackson.core:jackson-annotations:2.13.4 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/2.13.4/jackson-annotations-2.13.4-sources.jar (if published) |
| `jackson-core-2.13.4.jar` | com.fasterxml.jackson.core:jackson-core:2.13.4 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.13.4/jackson-core-2.13.4-sources.jar (if published) |
| `jackson-databind-2.13.4.2.jar` | com.fasterxml.jackson.core:jackson-databind:2.13.4.2 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.13.4.2/jackson-databind-2.13.4.2-sources.jar (if published) |
| `jackson-dataformat-msgpack-0.8.24.jar` | org.msgpack:jackson-dataformat-msgpack:0.8.24 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/msgpack/jackson-dataformat-msgpack/0.8.24/jackson-dataformat-msgpack-0.8.24-sources.jar (if published) |
| `jakarta.activation-api-2.1.2.jar` | jakarta.activation:jakarta.activation-api:2.1.2 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/jakarta/activation/jakarta.activation-api/2.1.2/jakarta.activation-api-2.1.2-sources.jar (if published) |
| `jakarta.xml.bind-api-4.0.0.jar` | jakarta.xml.bind:jakarta.xml.bind-api:4.0.0 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/jakarta/xml/bind/jakarta.xml.bind-api/4.0.0/jakarta.xml.bind-api-4.0.0-sources.jar (if published) |
| `jama-1.0.3.jar` | gov.nist.math:jama:1.0.3 | Public-Domain | permissive | https://repo1.maven.org/maven2/gov/nist/math/jama/1.0.3/jama-1.0.3-sources.jar (if published) |
| `java-cup-11b-20160615.jar` | com.github.vbmacher:java-cup:11b-20160615 | HPND-like (CUP license) | permissive | https://repo1.maven.org/maven2/com/github/vbmacher/java-cup/11b-20160615/java-cup-11b-20160615-sources.jar (if published) |
| `java-cup-runtime-11b-20160615.jar` | com.github.vbmacher:java-cup-runtime:11b-20160615 | HPND-like (CUP license) | permissive | https://repo1.maven.org/maven2/com/github/vbmacher/java-cup-runtime/11b-20160615/java-cup-runtime-11b-20160615-sources.jar (if published) |
| `javax.annotation-api-1.3.2.jar` | javax.annotation:javax.annotation-api:1.3.2 | CDDL-1.0 OR GPL-2.0-with-classpath-exception | weak-copyleft | `sources/corresponding-sources/javax.annotation-api-1.3.2-sources.jar` |
| `jaxb-core-4.0.3.jar` | org.glassfish.jaxb:jaxb-core:4.0.3 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/org/glassfish/jaxb/jaxb-core/4.0.3/jaxb-core-4.0.3-sources.jar (if published) |
| `jaxb-runtime-4.0.3.jar` | org.glassfish.jaxb:jaxb-runtime:4.0.3 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/org/glassfish/jaxb/jaxb-runtime/4.0.3/jaxb-runtime-4.0.3-sources.jar (if published) |
| `jclipboardhelper-0.1.0.jar` | com.github.fracpete:jclipboardhelper:0.1.0 | GPL-3.0 | strong-copyleft | `sources/corresponding-sources/jclipboardhelper-0.1.0-sources.jar` |
| `jfilechooser-bookmarks-0.1.6.jar` | com.github.fracpete:jfilechooser-bookmarks:0.1.6 | GPL-3.0 | strong-copyleft | `sources/corresponding-sources/jfilechooser-bookmarks-0.1.6-sources.jar` |
| `jgrapht-core-1.4.0.jar` | org.jgrapht:jgrapht-core:1.4.0 | LGPL-2.1 OR EPL-2.0 | weak-copyleft | `sources/corresponding-sources/jgrapht-core-1.4.0-sources.jar` |
| `jheaps-0.11.jar` | org.jheaps:jheaps:0.11 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/jheaps/jheaps/0.11/jheaps-0.11-sources.jar (if published) |
| `jniloader-1.1.jar` | com.github.fommil:jniloader:1.1 | LGPL-3.0 | weak-copyleft | `sources/corresponding-sources/jniloader-1.1-sources.jar` |
| `jspecify-1.0.0.jar` | org.jspecify:jspecify:1.0.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/jspecify/jspecify/1.0.0/jspecify-1.0.0-sources.jar (if published) |
| `jsr166y-1.7.0.jar` | org.codehaus.jsr166-mirror:jsr166y:1.7.0 | CC0-1.0 | permissive | https://repo1.maven.org/maven2/org/codehaus/jsr166-mirror/jsr166y/1.7.0/jsr166y-1.7.0-sources.jar (if published) |
| `jsr305-3.0.2.jar` | com.google.code.findbugs:jsr305:3.0.2 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/code/findbugs/jsr305/3.0.2/jsr305-3.0.2-sources.jar (if published) |
| `jul-to-slf4j-2.0.17.jar` | org.slf4j:jul-to-slf4j:2.0.17 | MIT | permissive | https://repo1.maven.org/maven2/org/slf4j/jul-to-slf4j/2.0.17/jul-to-slf4j-2.0.17-sources.jar (if published) |
| `listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar` | com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/google/guava/listenablefuture/9999.0-empty-to-avoid-conflict-with-guava/listenablefuture-9999.0-empty-to-avoid-conflict-with-guava-sources.jar (if published) |
| `log4j-api-2.24.0.jar` | org.apache.logging.log4j:log4j-api:2.24.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/logging/log4j/log4j-api/2.24.0/log4j-api-2.24.0-sources.jar (if published) |
| `log4j-core-2.24.0.jar` | org.apache.logging.log4j:log4j-core:2.24.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/logging/log4j/log4j-core/2.24.0/log4j-core-2.24.0-sources.jar (if published) |
| `log4j-slf4j2-impl-2.24.0.jar` | org.apache.logging.log4j:log4j-slf4j2-impl:2.24.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/apache/logging/log4j/log4j-slf4j2-impl/2.24.0/log4j-slf4j2-impl-2.24.0-sources.jar (if published) |
| `mmtf-api-1.0.11.jar` | org.rcsb:mmtf-api:1.0.11 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/rcsb/mmtf-api/1.0.11/mmtf-api-1.0.11-sources.jar (if published) |
| `mmtf-codec-1.0.11.jar` | org.rcsb:mmtf-codec:1.0.11 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/rcsb/mmtf-codec/1.0.11/mmtf-codec-1.0.11-sources.jar (if published) |
| `mmtf-serialization-1.0.11.jar` | org.rcsb:mmtf-serialization:1.0.11 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/rcsb/mmtf-serialization/1.0.11/mmtf-serialization-1.0.11-sources.jar (if published) |
| `msgpack-core-0.8.24.jar` | org.msgpack:msgpack-core:0.8.24 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/msgpack/msgpack-core/0.8.24/msgpack-core-0.8.24-sources.jar (if published) |
| `mtj-1.0.4.jar` | com.googlecode.matrix-toolkits-java:mtj:1.0.4 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/mtj-1.0.4-sources.jar` |
| `multiverse-core-0.7.0.jar` | org.multiverse:multiverse-core:0.7.0 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/multiverse/multiverse-core/0.7.0/multiverse-core-0.7.0-sources.jar (if published) |
| `native_ref-java-1.1.jar` | com.github.fommil.netlib:native_ref-java:1.1 | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/native_ref-java/1.1/native_ref-java-1.1-sources.jar (if published) |
| `native_system-java-1.1.jar` | com.github.fommil.netlib:native_system-java:1.1 | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/native_system-java/1.1/native_system-java-1.1-sources.jar (if published) |
| `netlib-java-1.1.jar` | com.googlecode.netlib-java:netlib-java:1.1 | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/googlecode/netlib-java/netlib-java/1.1/netlib-java-1.1-sources.jar (if published) |
| `netlib-native_ref-linux-armhf-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_ref-linux-armhf:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_ref-linux-armhf/1.1/netlib-native_ref-linux-armhf-1.1-sources.jar (if published) |
| `netlib-native_ref-linux-i686-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_ref-linux-i686:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_ref-linux-i686/1.1/netlib-native_ref-linux-i686-1.1-sources.jar (if published) |
| `netlib-native_ref-linux-x86_64-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_ref-linux-x86_64:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_ref-linux-x86_64/1.1/netlib-native_ref-linux-x86_64-1.1-sources.jar (if published) |
| `netlib-native_ref-osx-x86_64-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_ref-osx-x86_64:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_ref-osx-x86_64/1.1/netlib-native_ref-osx-x86_64-1.1-sources.jar (if published) |
| `netlib-native_ref-win-i686-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_ref-win-i686:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_ref-win-i686/1.1/netlib-native_ref-win-i686-1.1-sources.jar (if published) |
| `netlib-native_ref-win-x86_64-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_ref-win-x86_64:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_ref-win-x86_64/1.1/netlib-native_ref-win-x86_64-1.1-sources.jar (if published) |
| `netlib-native_system-linux-armhf-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_system-linux-armhf:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_system-linux-armhf/1.1/netlib-native_system-linux-armhf-1.1-sources.jar (if published) |
| `netlib-native_system-linux-i686-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_system-linux-i686:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_system-linux-i686/1.1/netlib-native_system-linux-i686-1.1-sources.jar (if published) |
| `netlib-native_system-linux-x86_64-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_system-linux-x86_64:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_system-linux-x86_64/1.1/netlib-native_system-linux-x86_64-1.1-sources.jar (if published) |
| `netlib-native_system-osx-x86_64-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_system-osx-x86_64:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_system-osx-x86_64/1.1/netlib-native_system-osx-x86_64-1.1-sources.jar (if published) |
| `netlib-native_system-win-i686-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_system-win-i686:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_system-win-i686/1.1/netlib-native_system-win-i686-1.1-sources.jar (if published) |
| `netlib-native_system-win-x86_64-1.1-natives.jar` | com.github.fommil.netlib:netlib-native_system-win-x86_64:1.1:natives | BSD-3-Clause | permissive | https://repo1.maven.org/maven2/com/github/fommil/netlib/netlib-native_system-win-x86_64/1.1/netlib-native_system-win-x86_64-1.1-sources.jar (if published) |
| `openchart-1.4.2.jar` | openchart:openchart:1.4.2 (JBoss thirdparty-releases repository, declared as a dependency by org.biojava.thirdparty:forester:1.039) | LGPL-2.1 | weak-copyleft | Upstream OpenChart project (approximatrix, SourceForge); artifact hosted at https://repository.jboss.org/nexus/content/repositories/thirdparty-releases/openchart/openchart/1.4.2/ (host outside the audit allowlist, not fetched) |
| `slf4j-api-2.0.17.jar` | org.slf4j:slf4j-api:2.0.17 | MIT | permissive | https://repo1.maven.org/maven2/org/slf4j/slf4j-api/2.0.17/slf4j-api-2.0.17-sources.jar (if published) |
| `txw2-4.0.3.jar` | org.glassfish.jaxb:txw2:4.0.3 | EDL-1.0 (BSD-3-Clause) | permissive | https://repo1.maven.org/maven2/org/glassfish/jaxb/txw2/4.0.3/txw2-4.0.3-sources.jar (if published) |
| `univocity-parsers-2.9.1.jar` | com.univocity:univocity-parsers:2.9.1 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/com/univocity/univocity-parsers/2.9.1/univocity-parsers-2.9.1-sources.jar (if published) |
| `vecmath-1.3.1.jar` | java3d:vecmath:1.3.1 | LicenseRef-Sun-restrictive-notice | unknown | https://repo1.maven.org/maven2/java3d/vecmath/1.3.1/vecmath-1.3.1-sources.jar (if published) |
| `vecmath-1.5.2.jar` | javax.vecmath:vecmath:1.5.2 | GPL-2.0-with-classpath-exception | strong-copyleft | `sources/corresponding-sources/vecmath-1.5.2-sources.jar` |
| `weka-dev-3.9.6.jar` | nz.ac.waikato.cms.weka:weka-dev:3.9.6 | GPL-3.0 | strong-copyleft | `sources/corresponding-sources/weka-dev-3.9.6-sources.jar` |
| `xom-1.3.9.jar` | xom:xom:1.3.9 | LGPL-2.1 | weak-copyleft | `sources/corresponding-sources/xom-1.3.9-sources.jar` |
| `xz-1.10.jar` | org.tukaani:xz:1.10 | 0BSD | permissive | https://repo1.maven.org/maven2/org/tukaani/xz/1.10/xz-1.10-sources.jar (if published) |
| `zstd-jni-1.5.7-4.jar` | com.github.luben:zstd-jni:1.5.7-4 | BSD-2-Clause | permissive | https://repo1.maven.org/maven2/com/github/luben/zstd-jni/1.5.7-4/zstd-jni-1.5.7-4-sources.jar (if published) |
| `zt-zip-1.17.jar` | org.zeroturnaround:zt-zip:1.17 | Apache-2.0 | permissive | https://repo1.maven.org/maven2/org/zeroturnaround/zt-zip/1.17/zt-zip-1.17-sources.jar (if published) |

## Other components

| Component | Version | License | Evidence | Source |
|---|---|---|---|---|
| 3Dmol.js | 2.5.5 | BSD-3-Clause | labs/binding-pockets/assets/LICENSE (sha256 4c6eaaed856f3f28a3b1a98e74f4a8a71618de7d51ea4155c29f6f793bcef861); npm tarball https://registry.npmjs.org/3dmol/-/3dmol-2.5.5.tgz (sources/3dmol-2.5.5.tgz) | https://github.com/3dmol/3Dmol.js (npm 3dmol@2.5.5) |
| gemmi | 0.7.3 | MPL-2.0 | https://raw.githubusercontent.com/project-gemmi/gemmi/v0.7.3/LICENSE.txt (sha256 fab3dd6bdab226f1c08630b1dd917e11fcb4ec5e1e020e2c16f83a0a13863e85); PyPI gemmi 0.7.3 license=MPL-2.0, classifier 'Mozilla Public License 2.0 (MPL 2.0)' | https://github.com/project-gemmi/gemmi/tree/v0.7.3 |
| jdk4py (bundled OpenJDK runtime) | 21.0.8.1 | GPL-2.0 WITH Classpath-exception-2.0 | PyPI https://pypi.org/pypi/jdk4py/21.0.8.1/json: license and license_expression fields empty; classifier 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'. Repository LICENSE https://raw.githubusercontent.com/activeviam/jdk4py/main/LICENSE (sha256 4b9abebc4338048a7c2dc184e9f800deb349366bdf28eb23c2677a77b4c87726) is byte-identical to https://raw.githubusercontent.com/openjdk/jdk21u/jdk-21.0.8-ga/LICENSE (GPLv2 + "CLASSPATH" EXCEPTION). | https://github.com/activeviam/jdk4py (wrapper; runtime built with jlink from Eclipse Temurin per .github/actions/build-java-runtime on main); OpenJDK 21 source: https://github.com/openjdk/jdk21u (tag jdk-21.0.8+9 / jdk-21.0.8-ga) |
| RCSB PDB fixtures 1CRN, 1STP, 7L13 | mmCIF as downloaded (labs/binding-pockets/fixtures, sources/*.cif) | CC0-1.0 | wwPDB usage policy https://www.wwpdb.org/about/usage-policies (PDB archive data are available under CC0 1.0) | https://www.rcsb.org/structure/1CRN, /1STP, /7L13 |

- **3Dmol.js**: Incorporates GLmol, Three.js and jQuery code; their notices are reproduced in assets/LICENSE.
- **gemmi**: Weak copyleft (file-level). Source for the release is at tag v0.7.3; no copy is retained in this repository.
- **jdk4py (bundled OpenJDK runtime)**: No 21.0.8.1 release tag exists in the jdk4py repo; the build workflow and LICENSE were read from the default branch at audit time. The PyPI classifier alone says GPLv2; the Classpath Exception is evidenced by the OpenJDK LICENSE text the project ships.
- **RCSB PDB fixtures 1CRN, 1STP, 7L13**: Derived PDB/mapping files in fixtures/ are generated from these entries.

## Corresponding source for copyleft components

For each GPL/LGPL/EPL/CDDL jar below, the source for the exact distributed version was retained under `sources/corresponding-sources/` (repository root `models/models-p2rank/`) and is also published at the listed URL. Maven Central `-sources.jar` files belong to the byte-identical Central artifact (SHA-1 verified). GitHub tarballs are the commit archives of the matching upstream tag/commit; GitHub does not guarantee archive byte-stability, so the sha256 identifies the retained copy. Shipping these files alongside the binaries (or an equivalent offer under each license) is the distributor's responsibility; this record is not itself a written offer.

| Jar | License | Corresponding source | sha256 | Bytes |
|---|---|---|---|---|
| `biojava-alignment-7.2.2.jar` | LGPL-2.1 | `sources/corresponding-sources/biojava-alignment-7.2.2-sources.jar` ← https://repo1.maven.org/maven2/org/biojava/biojava-alignment/7.2.2/biojava-alignment-7.2.2-sources.jar | `7f0b6f6814730baf…` | 120428 |
| `biojava-core-7.2.2.jar` | LGPL-2.1 | `sources/corresponding-sources/biojava-core-7.2.2-sources.jar` ← https://repo1.maven.org/maven2/org/biojava/biojava-core/7.2.2/biojava-core-7.2.2-sources.jar | `55ff266ddc7893d6…` | 403853 |
| `biojava-structure-7.2.2-rdk.1.jar` | LGPL-2.1 | `sources/corresponding-sources/biojava-7.2.2-rdk.1-49c633adae29.tar.gz` ← https://api.github.com/repos/rdk/biojava/tarball/49c633adae29f9fea58395b4c896e478b677e899 | `9ba4b460f58335ca…` | 17901906 |
| `cdk-atomtype-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-atomtype-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-atomtype/2.11/cdk-atomtype-2.11-sources.jar | `df35cee62c4fba55…` | 24961 |
| `cdk-charges-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-charges-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-charges/2.11/cdk-charges-2.11-sources.jar | `44014b57b51dd36d…` | 29259 |
| `cdk-core-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-core-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-core/2.11/cdk-core-2.11-sources.jar | `4d30c22289707e8a…` | 271925 |
| `cdk-ctab-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-ctab-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-ctab/2.11/cdk-ctab-2.11-sources.jar | `7cad1059840e0825…` | 118916 |
| `cdk-dict-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-dict-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-dict/2.11/cdk-dict-2.11-sources.jar | `a7ca85de06f8d263…` | 36999 |
| `cdk-fingerprint-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-fingerprint-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-fingerprint/2.11/cdk-fingerprint-2.11-sources.jar | `97048dad9761f2e2…` | 106700 |
| `cdk-formula-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-formula-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-formula/2.11/cdk-formula-2.11-sources.jar | `25a6ad5206490559…` | 65295 |
| `cdk-fragment-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-fragment-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-fragment/2.11/cdk-fragment-2.11-sources.jar | `226f04f680410a1d…` | 24528 |
| `cdk-hash-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-hash-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-hash/2.11/cdk-hash-2.11-sources.jar | `5172881381a54223…` | 72431 |
| `cdk-interfaces-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-interfaces-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-interfaces/2.11/cdk-interfaces-2.11-sources.jar | `11117af94d658e07…` | 135879 |
| `cdk-ioformats-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-ioformats-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-ioformats/2.11/cdk-ioformats-2.11-sources.jar | `20e31eca51bdf876…` | 123179 |
| `cdk-isomorphism-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-isomorphism-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-isomorphism/2.11/cdk-isomorphism-2.11-sources.jar | `144ae5e41deb204c…` | 120320 |
| `cdk-qsar-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-qsar-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-qsar/2.11/cdk-qsar-2.11-sources.jar | `bdea418a69f7437d…` | 45913 |
| `cdk-qsarmolecular-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-qsarmolecular-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-qsarmolecular/2.11/cdk-qsarmolecular-2.11-sources.jar | `e9059411497c0434…` | 208951 |
| `cdk-reaction-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-reaction-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-reaction/2.11/cdk-reaction-2.11-sources.jar | `2d5f58c762d707b1…` | 134517 |
| `cdk-silent-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-silent-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-silent/2.11/cdk-silent-2.11-sources.jar | `8ae371ca1144bb77…` | 109552 |
| `cdk-smarts-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-smarts-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-smarts/2.11/cdk-smarts-2.11-sources.jar | `e5d68c5d4295d351…` | 55393 |
| `cdk-smiles-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-smiles-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-smiles/2.11/cdk-smiles-2.11-sources.jar | `26ba1602144a79b9…` | 60793 |
| `cdk-standard-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-standard-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-standard/2.11/cdk-standard-2.11-sources.jar | `e6339e4f4e43d757…` | 299611 |
| `cdk-valencycheck-2.11.jar` | LGPL-2.1 | `sources/corresponding-sources/cdk-valencycheck-2.11-sources.jar` ← https://repo1.maven.org/maven2/org/openscience/cdk/cdk-valencycheck/2.11/cdk-valencycheck-2.11-sources.jar | `ce561389464b6543…` | 23023 |
| `faster-molecular-surface-1.0.jar` | LGPL-2.1 | `sources/corresponding-sources/FasterMolecularSurface-1.0-207cc34debc4.tar.gz` ← https://api.github.com/repos/rdk/FasterMolecularSurface/tarball/207cc34debc41f50bab1d879d08da88da9309763 | `11786971291607d9…` | 72776 |
| `FasterForest-2.5.2.jar` | GPL-2.0 | `sources/corresponding-sources/FasterForest-2.5.2-246546ac8c18.tar.gz` ← https://api.github.com/repos/rdk/FasterForest/tarball/246546ac8c184c16dc2f432e8d1d5256776e0b7d | `162e1bdb80b979ce…` | 780768 |
| `FastRandomForest_0.99.jar` | GPL-2.0 | `sources/p2rank_2.5.1/bin/lib/FastRandomForest_0.99_src.jar` ← bin/lib/FastRandomForest_0.99_src.jar (shipped inside the P2Rank 2.5.1 distribution); mirror https://raw.githubusercontent.com/rdk/p2rank/9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e/lib/FastRandomForest_0.99_src.jar | `9a92d5ef38a3a387…` | 53036 |
| `FastRandomForest_0.99_src.jar` | GPL-2.0 | `sources/p2rank_2.5.1/bin/lib/FastRandomForest_0.99_src.jar` ← bin/lib/FastRandomForest_0.99_src.jar (shipped inside the P2Rank 2.5.1 distribution); mirror https://raw.githubusercontent.com/rdk/p2rank/9808a7723be9a94e2ffc21ab5f724cb6ae4ba01e/lib/FastRandomForest_0.99_src.jar | `9a92d5ef38a3a387…` | 53036 |
| `forester-1.039.jar` | LGPL-2.1 | `sources/corresponding-sources/forester-1.039-sources.jar` ← https://repo1.maven.org/maven2/org/biojava/thirdparty/forester/1.039/forester-1.039-sources.jar | `03fe17695618ac94…` | 1073861 |
| `javax.annotation-api-1.3.2.jar` | CDDL-1.0 OR GPL-2.0-with-classpath-exception | `sources/corresponding-sources/javax.annotation-api-1.3.2-sources.jar` ← https://repo1.maven.org/maven2/javax/annotation/javax.annotation-api/1.3.2/javax.annotation-api-1.3.2-sources.jar | `128971e52e0d84a6…` | 42279 |
| `jclipboardhelper-0.1.0.jar` | GPL-3.0 | `sources/corresponding-sources/jclipboardhelper-0.1.0-sources.jar` ← https://repo1.maven.org/maven2/com/github/fracpete/jclipboardhelper/0.1.0/jclipboardhelper-0.1.0-sources.jar | `16617399fb8675e2…` | 8116 |
| `jfilechooser-bookmarks-0.1.6.jar` | GPL-3.0 | `sources/corresponding-sources/jfilechooser-bookmarks-0.1.6-sources.jar` ← https://repo1.maven.org/maven2/com/github/fracpete/jfilechooser-bookmarks/0.1.6/jfilechooser-bookmarks-0.1.6-sources.jar | `f22022e131fb66d7…` | 34099 |
| `jgrapht-core-1.4.0.jar` | LGPL-2.1 OR EPL-2.0 | `sources/corresponding-sources/jgrapht-core-1.4.0-sources.jar` ← https://repo1.maven.org/maven2/org/jgrapht/jgrapht-core/1.4.0/jgrapht-core-1.4.0-sources.jar | `e409f940e3a01342…` | 894621 |
| `jniloader-1.1.jar` | LGPL-3.0 | `sources/corresponding-sources/jniloader-1.1-sources.jar` ← https://repo1.maven.org/maven2/com/github/fommil/jniloader/1.1/jniloader-1.1-sources.jar | `f31f1d3d257c1c29…` | 4441 |
| `mtj-1.0.4.jar` | LGPL-2.1 | `sources/corresponding-sources/mtj-1.0.4-sources.jar` ← https://repo1.maven.org/maven2/com/googlecode/matrix-toolkits-java/mtj/1.0.4/mtj-1.0.4-sources.jar | `b98ddcdc67cdd3de…` | 210588 |
| `openchart-1.4.2.jar` | LGPL-2.1 | MISSING (no exact source located) | - | - |
| `vecmath-1.5.2.jar` | GPL-2.0-with-classpath-exception | `sources/corresponding-sources/vecmath-1.5.2-sources.jar` ← https://repo1.maven.org/maven2/javax/vecmath/vecmath/1.5.2/vecmath-1.5.2-sources.jar | `7bea4e97b737757c…` | 183220 |
| `weka-dev-3.9.6.jar` | GPL-3.0 | `sources/corresponding-sources/weka-dev-3.9.6-sources.jar` ← https://repo1.maven.org/maven2/nz/ac/waikato/cms/weka/weka-dev/3.9.6/weka-dev-3.9.6-sources.jar | `35ae9419c3060bfc…` | 7721859 |
| `xom-1.3.9.jar` | LGPL-2.1 | `sources/corresponding-sources/xom-1.3.9-sources.jar` ← https://repo1.maven.org/maven2/xom/xom/1.3.9/xom-1.3.9-sources.jar | `21c54a2c66bbd73b…` | 312377 |

Total downloaded corresponding source: 31,833,337 bytes in 35 files (plus `bin/lib/FastRandomForest_0.99_src.jar`, 53,036 bytes, shipped inside the P2Rank distribution).

Gemmi (MPL-2.0) and the jdk4py OpenJDK runtime (GPL-2.0 with Classpath Exception) source locations are listed in Other components; no copies are retained under `sources/corresponding-sources/`.
