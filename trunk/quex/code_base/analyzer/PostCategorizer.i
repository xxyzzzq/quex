/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__POST_CATEGORIZER_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__POST_CATEGORIZER_I__
#ifdef  QUEX_OPTION_POST_CATEGORIZER

#include <quex/code_base/MemoryManager>
#include <quex/code_base/analyzer/PostCategorizer>

#ifndef __QUEX_SETTING_PLAIN_C
namespace quex {
#endif

#   ifndef __QUEX_SETTING_PLAIN_C
    QUEX_INLINE void
    QuexPostCategorizer::enter(const QUEX_TYPE_CHARACTER* Lexeme, const QUEX_TYPE_TOKEN_ID TokenID)
    {
        QuexPostCategorizer_enter(this, Lexeme, TokenID);
    }
    
    QUEX_INLINE void
    QuexPostCategorizer::remove(const QUEX_TYPE_CHARACTER* Lexeme)
    {
        QuexPostCategorizer_remove(this, Lexeme);
    }

    QUEX_INLINE QUEX_TYPE_TOKEN_ID 
    QuexPostCategorizer::get_token_id(const QUEX_TYPE_CHARACTER* Lexeme) const
    {
        QuexPostCategorizerNode* found = QuexPostCategorizer_find(this, Lexeme);
        if( found == 0x0 ) return __QUEX_SETTING_TOKEN_ID_UNINITIALIZED;
        return found->token_id;
    }
#   endif

    QUEX_INLINE void
    QuexPostCategorizer::clear()
    {
        QuexPostCategorizer_clear(this, root);
    }

    QUEX_INLINE QuexPostCategorizerNode* 
    QuexPostCategorizerNode_new(QUEX_TYPE_CHARACTER         FirstCharacter,
                                const QUEX_TYPE_CHARACTER*  Remainder,
                                QUEX_TYPE_TOKEN_ID          TokenID)
    {
        QuexPostCategorizerNode* me = MemoryManager_PostCategorizerNode_allocate(__QUEX_STD_strlen(Remainder));
        me->name_first_character = FirstCharacter;
        me->name_remainder       = Remainder;
        me->token_id             = TokenID;
        me->lesser  = 0x0;
        me->greater = 0x0;
        return me;
    }

    QUEX_INLINE int
    QuexPostCategorizerNode_compare(QuexPostCategorizerNode*    me, 
                                    QUEX_TYPE_CHARACTER         FirstCharacter, 
                                    const QUEX_TYPE_CHARACTER*  Remainder)
    {
        if     ( FirstCharacter > me->name_first_character ) return 1;
        else if( FirstCharacter < me->name_first_character ) return -1;
        else                                                 return strcmp(Remainder, me->name_remainder);
    }

    QUEX_INLINE void
    QuexPostCategorizer_construct(QuexPostCategorizer* me)
    {
        me->root = 0x0;
    }

    QUEX_INLINE QuexPostCategorizerNode*
    QuexPostCategorizer_find(const QuexPostCategorizer* me, const QUEX_TYPE_CHARACTER* EntryName)
    {
        QUEX_TYPE_CHARACTER         FirstCharacter = EntryName[0];
        const QUEX_TYPE_CHARACTER*  Remainder = FirstCharacter == 0x0 ? 0x0 : EntryName + 1;
        QuexPostCategorizerNode*    node = me->root;

        while( node != 0x0 ) {
            int result = QuexPostCategorizerNode_compare(node, FirstCharacter, Remainder);
            if     ( result == 1 )  node = node->greater;
            else if( result == -1 ) node = node->lesser;
            else                    return node;
        }
        return 0x0;
    }

    QUEX_INLINE void
    QuexPostCategorizer_enter(QuexPostCategorizer* me, 
                              const QUEX_TYPE_CHARACTER* EntryName, QUEX_TYPE_TOKEN_ID TokenID)
    {
        QUEX_TYPE_CHARACTER         FirstCharacter = EntryName[0];
        const QUEX_TYPE_CHARACTER*  Remainder = FirstCharacter == 0x0 ? 0x0 : EntryName + 1;
        QuexPostCategorizerNode*    node      = me->root;
        QuexPostCategorizerNode*    prev_node = 0x0;
        int                         result = 0;

        if( me->root == 0x0 ) {
            me->root = QuexPostCategorizerNode_new(FirstCharacter, Remainder, TokenID);
            return;
        }
        while( node != 0x0 ) {
            prev_node = node;
            result    = QuexPostCategorizerNode_compare(node, FirstCharacter, Remainder);
            if     ( result == 1 )  node = node->greater;
            else if( result == -1 ) node = node->lesser;
            else                    return; /* Node with that name already exists */
        }
        __quex_assert( prev_node != 0x0 );
        __quex_assert( result != 0 );

        if( result == 1 ) 
            prev_node->greater = QuexPostCategorizerNode_new(FirstCharacter, Remainder, TokenID);
        else 
            prev_node->lesser  = QuexPostCategorizerNode_new(FirstCharacter, Remainder, TokenID);
    }

    QUEX_INLINE void
    QuexPostCategorizer_remove(QuexPostCategorizer* me, const QUEX_TYPE_CHARACTER* EntryName)
    {
        int result = 0;
        QUEX_TYPE_CHARACTER         FirstCharacter = EntryName[0];
        const QUEX_TYPE_CHARACTER*  Remainder = FirstCharacter == 0x0 ? 0x0 : EntryName + 1;
        QuexPostCategorizerNode*    node   = 0x0;
        QuexPostCategorizerNode*  parent = 0x0;
        QuexPostCategorizerNode*  found  = me->root;

        __quex_assert( found != 0x0 );
        while( 1 + 1 == 2 ) {
            result = QuexPostCategorizerNode_compare(found, FirstCharacter, Remainder);
           
            /* result == 0: found's name == EntryName 
             * On 'break': If found == root then parent = 0x0 which triggers a special treatment. */
            if( result == 0 ) break;

            parent = found;

            if     ( result == 1 )  found = found->greater;
            else if( result == -1 ) found = found->lesser;

            if( found == 0x0 ) return; /* Not found name with that name */
        };
        /* Found a node with 'EntryName' */

        /* Remove node and re-order tree */
        if( parent == 0x0 ) {
            if( found->lesser != 0x0 ) {
                for(node = found->lesser; node->greater != 0x0; node = node->greater );
                node->greater = found->greater;
                me->root      = found->lesser;
            } else {
                me->root      = found->greater;
            }
        }
        else if( found == parent->lesser ) {
            /* (1) 'found' is the 'lesser' child of the parent:
             *
             *                 (parent's greater tree)
             *                /
             *        (parent)        (greater tree)
             *               \       /
             *                (found)
             *                       \
             *                        (lesser tree)
             *
             *     All subnodes of (greater tree) are greater than all subnodes in (lesser tree).
             *     => (i) mount (lesser tree) to the least node of (greater tree).                
             *     Anything in the subtree of 'found' is lesser than anything in 'parent's 
             *     greater tree.
             *     => (ii) mount (greater tree) to the least node of the (parent's greater tree). */
            /* parent != 0x0, see above */
            if( found->greater != 0x0 ) {
                for(node = found->greater; node->lesser != 0x0; node = node->lesser );
                node->lesser   = found->lesser;
                parent->lesser = found->greater;
            } else {
                parent->lesser = found->lesser;
            }

        } else {
            /* (2) 'found' is the 'greater' child of the parent:
             *
             *     (i)  mount (greater tree) to the greatest node of (greater tree).                  
             *     (ii) mount (lesser tree) to the greatest node of the (parent's lesser tree). */
            /* parent != 0x0, see above */
            if( found->lesser != 0x0 ) {
                for(node = found->lesser; node->greater != 0x0; node = node->greater );
                node->greater   = found->greater;
                parent->greater = found->lesser;
            } else {
                parent->greater = found->greater;
            }
        }
        MemoryManager_PostCategorizerNode_free(found);
    }

    QUEX_INLINE void
    QuexPostCategorizer_print_tree(QuexPostCategorizerNode* node, int Depth)
    {
        if( node == 0x0 ) {
            for(int i=0; i<Depth; ++i) __QUEX_STD_printf("        ");
            __QUEX_STD_printf("[EMPTY]\n");
            return;
        }

        QuexPostCategorizer_print_tree(node->greater, Depth + 1);

        for(int i=0; i < Depth + 1; ++i) __QUEX_STD_printf("        ");
        __QUEX_STD_printf("/\n");

        for(int i=0; i<Depth; ++i) __QUEX_STD_printf("        ");
        __QUEX_STD_printf("[%c]%s: %i\n", node->name_first_character, node->name_remainder, (int)node->token_id);

        for(int i=0; i<Depth + 1; ++i) __QUEX_STD_printf("        ");
        __QUEX_STD_printf("\\\n");

        QuexPostCategorizer_print_tree(node->lesser, Depth + 1);
    }

    QUEX_INLINE void
    QuexPostCategorizer_clear(QuexPostCategorizer* me, QuexPostCategorizerNode* branch)
    {
        if( branch == 0x0 ) branch = me->root;
        if( branch->lesser  != 0x0 ) QuexPostCategorizer_clear(me, branch->lesser);
        if( branch->greater != 0x0 ) QuexPostCategorizer_clear(me, branch->greater);
        MemoryManager_PostCategorizerNode_free(branch);
    }

#ifndef __QUEX_SETTING_PLAIN_C
} // namespace quex
#endif

#include <quex/code_base/MemoryManager.i>

#endif /* QUEX_OPTION_POST_CATEGORIZER */
#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__POST_CATEGORIZER_I__ */
