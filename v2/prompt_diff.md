# Prompt Diff — Permissive vs Strict
Testing 3 queries: in-scope direct, paraphrased, out-of-scope.
Retriever used: BM25
============================================================

## [IN-SCOPE DIRECT]
**Question:** State the law of conservation of momentum.

### Permissive prompt response
The law of conservation of momentum states that the total momentum of a closed system (where there is no external unbalanced force acting on them) remains constant. In other words, the sum of momenta of the objects before collision is equal to the sum of momenta after the collision. This can also be stated as the total momentum of the objects is unchanged or conserved by the collision.

### Strict prompt response
The law of conservation of momentum states that the sum of momenta of the two objects before collision is equal to the sum of momenta after the collision provided there is no external unbalanced force acting on them [0eb67c7a-074].

**Refusal triggered:** False  
**Cited chunk_ids:** ['0eb67c7a-074', '09be8252-a54', '4bdb05e2-8db', '57dfe5fa-876', '4c61b2bb-833']

------------------------------------------------------------

## [PARAPHRASED]
**Question:** Why does a moving ball eventually stop on its own?

### Permissive prompt response
A moving ball eventually stops on its own due to the force of friction, which opposes the motion of the ball. As the ball moves, it experiences frictional forces from the ground, air resistance, and other external factors that slow it down. The force of friction converts the kinetic energy of the ball into heat energy, causing the ball to lose its energy and eventually come to rest. This process is a demonstration of the law of conservation of energy, where the energy of the ball is transformed from one form (kinetic energy) to another (heat energy), but the total energy remains conserved.

### Strict prompt response
I don't have that in my study materials.

**Refusal triggered:** True  
**Cited chunk_ids:** ['a4fe4191-aa2', 'd6b31710-c79', '31d93292-f57', 'ff733501-fd0', '352d565b-a44']

------------------------------------------------------------

## [OUT-OF-SCOPE]
**Question:** Explain Einstein's theory of special relativity.

### Permissive prompt response
The context provided does not mention Einstein's theory of special relativity. The context appears to be related to the chapter "Atoms and Molecules" and "Structure of the Atom" from the NCERT Class 9 Science textbook, and it discusses topics such as Dalton's atomic theory, the law of conservation of mass, and the structure of atoms.

However, I can provide a general explanation of Einstein's theory of special relativity, which is not directly related to the context provided.

Einstein's theory of special relativity, introduced in 1905, challenged the long-held notion of absolute time and space. The theory postulates that the laws of physics are the same for all observers in uniform motion relative to one another. The theory is based on two main principles:

1. The laws of physics are the same for all observers in uniform motion relative to one another.
2. The speed of light is always constant, regardless of the motion of the observer or the source of light.

From these principles, Einstein derived several key consequences, including:

* Time dilation: Time appears to pass slower for an observer in motion relative to a stationary observer.
* Length contraction: Objects appear shorter to an observer in motion relative to a stationary observer.
* Relativity of simultaneity: Two events that are simultaneous for one observer may not be simultaneous for another observer in a different state of motion.
* Equivalence of mass and energy: Mass and energy are interchangeable, as expressed by the famous equation E = mc^2.

Einstein's theory of special relativity revolutionized our understanding of space and time, and it has had a profound impact on the development of modern physics. However, please note that this topic is not directly related to the context provided, which focuses on atoms and molecules.

### Strict prompt response
I don't have that in my study materials.

**Refusal triggered:** True  
**Cited chunk_ids:** ['42267ade-082', '555f2fd8-14f', 'f286cfc9-fc2', '6af81910-874', 'd2f687ce-eee']

------------------------------------------------------------
